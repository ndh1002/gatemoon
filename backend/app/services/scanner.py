from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Signal, Symbol, TickerSnapshot
from app.db.session import get_session_factory
from app.services.gate_client import GateClient
from app.services.hub import MarketHub
from app.services.risk import compute_risk_score
from app.services.scoring import compute_scores, ohlcv_features
from app.services.social import meme_trend_score, social_velocity_score
from app.services.telegram_alerts import maybe_send_alert
from app.services.whale import whale_metrics

logger = logging.getLogger(__name__)


def _parse_quote_volume(t: dict[str, Any]) -> float:
    try:
        return float(t.get("quoteVolume") or t.get("info", {}).get("quote_volume") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ensure_symbol(db: Session, market: str) -> Symbol:
    parts = market.split("/")
    base = parts[0] if parts else market
    quote = parts[1] if len(parts) > 1 else ""
    sym = db.execute(select(Symbol).where(Symbol.market == market)).scalar_one_or_none()
    if sym:
        return sym
    sym = Symbol(exchange="gate", market=market, base=base, quote=quote)
    db.add(sym)
    db.flush()
    return sym


def _load_quote_volume_history(db: Session, symbol_id: int, limit: int = 24) -> list[float]:
    rows = db.execute(
        select(TickerSnapshot.quote_volume)
        .where(TickerSnapshot.symbol_id == symbol_id)
        .order_by(TickerSnapshot.ts.desc())
        .limit(limit)
    ).scalars().all()
    return [float(x) for x in rows if x is not None]


def _persist(db: Session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        market = row["symbol"]
        sym = _ensure_symbol(db, market)
        t = row["ticker"]
        snap = TickerSnapshot(
            symbol_id=sym.id,
            last=_f(t.get("last")),
            base_volume=_f(t.get("baseVolume")),
            quote_volume=_f(t.get("quoteVolume")),
            bid=_f(t.get("bid")),
            ask=_f(t.get("ask")),
            high=_f(t.get("high")),
            low=_f(t.get("low")),
            change_pct=_f(t.get("percentage")),
            vwap=_f(t.get("vwap")),
        )
        db.add(snap)
        sig = Signal(
            symbol_id=sym.id,
            moonshot_score=float(row["moonshot_score"]),
            confidence=float(row["confidence"]),
            risk_score=float(row["risk_score"]),
            details=row.get("details", {}),
        )
        db.add(sig)
    db.commit()


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


async def run_scanner(hub: MarketHub, redis_client: redis.Redis | None) -> None:
    settings = get_settings()
    client = GateClient()
    session_factory = get_session_factory()
    try:
        while True:
            try:
                tickers = await client.fetch_tickers()
            except Exception as exc:  # pragma: no cover
                logger.exception("fetch_tickers failed: %s", exc)
                await asyncio.sleep(settings.scan_interval_seconds)
                continue

            candidates: list[tuple[str, dict[str, Any], float]] = []
            for market, t in tickers.items():
                if not market.endswith("/USDT"):
                    continue
                qv = _parse_quote_volume(t)
                if qv < settings.min_quote_volume_usdt:
                    continue
                candidates.append((market, t, qv))
            candidates.sort(key=lambda x: x[2], reverse=True)
            top = candidates[: settings.top_symbols_by_quote_volume]

            histories: dict[str, list[float]] = {}
            with session_factory() as db:
                for market, _, _ in top:
                    sym = db.execute(select(Symbol).where(Symbol.market == market)).scalar_one_or_none()
                    if sym is None:
                        histories[market] = []
                    else:
                        histories[market] = _load_quote_volume_history(db, sym.id)

            sem = asyncio.Semaphore(12)

            async def one(market: str, ticker: dict[str, Any]) -> dict[str, Any] | None:
                async with sem:
                    try:
                        ohlcv, trades = await asyncio.gather(
                            client.fetch_ohlcv(market, timeframe="1h", limit=48),
                            client.fetch_trades(market, limit=120),
                        )
                    except Exception as exc:
                        logger.warning("fetch detail failed %s: %s", market, exc)
                        return None
                    w_score, w_conc = whale_metrics(trades)
                    base = market.split("/")[0]
                    soc_vel, soc_src = await social_velocity_score(base)
                    bid = float(ticker.get("bid") or 0.0)
                    ask = float(ticker.get("ask") or 0.0)
                    mid = (bid + ask) / 2.0 if bid and ask else float(ticker.get("last") or 0.0)
                    spread_pct = float((ask - bid) / mid * 100.0) if mid > 0 and bid and ask else 0.5
                    ohlc = ohlcv_features(ohlcv)
                    ohlc_parts_vol = ohlc["volatility"]
                    change_pct = abs(float(ticker.get("percentage") or 0.0))
                    meme_kw = meme_trend_score(base) > 0.35
                    risk_val, risk_break = compute_risk_score(
                        spread_pct=spread_pct,
                        volatility_1h=ohlc_parts_vol,
                        change_pct_abs=change_pct,
                        volume_usdt=_parse_quote_volume(ticker),
                        meme_keyword=meme_kw,
                        whale_concentration=w_conc,
                    )
                    scores = compute_scores(
                        ticker=ticker,
                        ohlcv=ohlcv,
                        trades=trades,
                        quote_volume_history=histories.get(market, []),
                        social_velocity=soc_vel,
                        whale_score=w_score,
                        risk_score=risk_val,
                    )
                    return {
                        "symbol": market,
                        "ticker": {
                            "symbol": market,
                            "last": ticker.get("last"),
                            "quoteVolume": ticker.get("quoteVolume"),
                            "baseVolume": ticker.get("baseVolume"),
                            "percentage": ticker.get("percentage"),
                            "bid": ticker.get("bid"),
                            "ask": ticker.get("ask"),
                            "high": ticker.get("high"),
                            "low": ticker.get("low"),
                        },
                        "moonshot_score": scores["moonshot_score"],
                        "confidence": scores["confidence"],
                        "risk_score": scores["risk_score"],
                        "details": scores["details"],
                        "risk_breakdown": risk_break,
                        "social_source": soc_src,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }

            gathered = await asyncio.gather(*[one(m, t) for m, t, _ in top])
            rows = [g for g in gathered if g is not None]
            rows.sort(key=lambda r: r["moonshot_score"], reverse=True)

            def _persist_sync() -> None:
                with session_factory() as db:
                    try:
                        persist_rows = [
                            {
                                "symbol": r["symbol"],
                                "ticker": r["ticker"],
                                "moonshot_score": r["moonshot_score"],
                                "confidence": r["confidence"],
                                "risk_score": r["risk_score"],
                                "details": {
                                    **r["details"],
                                    "risk_breakdown": r["risk_breakdown"],
                                    "social_source": r["social_source"],
                                    "quote_volume": (r.get("ticker") or {}).get("quoteVolume"),
                                },
                            }
                            for r in rows
                        ]
                        if persist_rows:
                            _persist(db, persist_rows)
                    except Exception as exc:
                        logger.exception("persist failed: %s", exc)
                        db.rollback()

            await asyncio.to_thread(_persist_sync)

            payload = {
                "type": "market_scan",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(rows),
                "rows": rows,
            }
            await hub.broadcast_json(payload)
            if redis_client is not None:
                try:
                    await redis_client.set("moonhunter:latest_scan", json.dumps(payload, default=str), ex=180)
                except Exception as exc:
                    logger.warning("redis set failed: %s", exc)

            for r in rows[:25]:
                asyncio.create_task(
                    maybe_send_alert(
                        session_factory,
                        symbol_market=r["symbol"],
                        moonshot=float(r["moonshot_score"]),
                        risk=float(r["risk_score"]),
                        confidence=float(r["confidence"]),
                        details=r["details"],
                    )
                )

            await asyncio.sleep(settings.scan_interval_seconds)
    finally:
        await client.close()
