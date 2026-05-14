from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import AlertLog, Signal, Symbol
from app.db.session import get_db

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gate-moonhunter-api"}


async def _latest_payload(request: Request) -> dict[str, Any]:
    r = getattr(request.app.state, "redis", None)
    if r is None:
        return {"type": "empty", "rows": [], "generated_at": None}
    raw = await r.get("moonhunter:latest_scan")
    if not raw:
        return {"type": "empty", "rows": [], "generated_at": None}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    return json.loads(raw)


@router.get("/latest")
async def latest(request: Request) -> dict[str, Any]:
    return await _latest_payload(request)


@router.get("/signals")
def list_signals(db: Session = Depends(get_db), limit: int = 200) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Signal, Symbol)
        .join(Symbol, Signal.symbol_id == Symbol.id)
        .order_by(desc(Signal.ts))
        .limit(limit)
    ).all()
    out: list[dict[str, Any]] = []
    for sig, sym in rows:
        out.append(
            {
                "market": sym.market,
                "moonshot_score": sig.moonshot_score,
                "confidence": sig.confidence,
                "risk_score": sig.risk_score,
                "details": sig.details,
                "ts": sig.ts.isoformat() if sig.ts else None,
            }
        )
    return out


@router.get("/top-moonshots")
async def top_moonshots(request: Request, limit: int = 40) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = data.get("rows") or []
    return rows[:limit]


@router.get("/moonshots_test")
async def moonshots(
    request: Request,
    limit: int = 40,
    min_score: float = 0.0,
    max_risk: float = 100.0,
) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = data.get("rows") or []
    out: list[dict[str, Any]] = []
    for row in rows:
        moon = float(row.get("moonshot_score") or 0.0)
        risk = float(row.get("risk_score") or 0.0)
        if moon >= min_score and risk <= max_risk:
            out.append(row)
    return out[:limit]


@router.get("/top-volume")
async def top_volume(request: Request, limit: int = 40) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = list(data.get("rows") or [])
    rows.sort(
        key=lambda r: float((r.get("ticker") or {}).get("quoteVolume") or 0.0),
        reverse=True,
    )
    out: list[dict[str, Any]] = []
    for r in rows[:limit]:
        t = r.get("ticker") or {}
        out.append(
            {
                "market": r.get("symbol"),
                "quote_volume": t.get("quoteVolume"),
                "moonshot_score": r.get("moonshot_score"),
                "risk_score": r.get("risk_score"),
                "ts": r.get("ts"),
            }
        )
    return out


@router.get("/top-gainers")
async def top_gainers(request: Request, limit: int = 40) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = list(data.get("rows") or [])
    rows.sort(key=lambda r: float((r.get("ticker") or {}).get("percentage") or 0.0), reverse=True)
    return rows[:limit]


@router.get("/heatmap")
async def heatmap(request: Request, limit: int = 80) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = list(data.get("rows") or [])[:limit]
    out: list[dict[str, Any]] = []
    for row in rows:
        ticker = row.get("ticker") or {}
        out.append(
            {
                "symbol": row.get("symbol"),
                "moonshot_score": row.get("moonshot_score"),
                "risk_score": row.get("risk_score"),
                "change_pct": ticker.get("percentage"),
                "quote_volume": ticker.get("quoteVolume"),
                "confidence": row.get("confidence"),
                "ts": row.get("ts"),
            }
        )
    return out


@router.get("/smart-money")
async def smart_money(request: Request, limit: int = 40) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = list(data.get("rows") or [])
    rows.sort(key=lambda r: float((r.get("details") or {}).get("smart_money") or 0.0), reverse=True)
    out: list[dict[str, Any]] = []
    for row in rows[:limit]:
        d = row.get("details") or {}
        out.append(
            {
                "symbol": row.get("symbol"),
                "smart_money": d.get("smart_money"),
                "whale_activity": d.get("whale_activity"),
                "moonshot_score": row.get("moonshot_score"),
                "risk_score": row.get("risk_score"),
                "confidence": row.get("confidence"),
                "ts": row.get("ts"),
            }
        )
    return out


@router.get("/risk-analysis")
async def risk_analysis(request: Request, limit: int = 40) -> list[dict[str, Any]]:
    data = await _latest_payload(request)
    rows = list(data.get("rows") or [])
    rows.sort(key=lambda r: float(r.get("risk_score") or 0.0), reverse=True)
    out: list[dict[str, Any]] = []
    for row in rows[:limit]:
        d = row.get("details") or {}
        out.append(
            {
                "symbol": row.get("symbol"),
                "risk_score": row.get("risk_score"),
                "moonshot_score": row.get("moonshot_score"),
                "confidence": row.get("confidence"),
                "risk_breakdown": d.get("risk_breakdown", {}),
                "spread_risk": (d.get("risk_breakdown") or {}).get("spread"),
                "volatility_risk": (d.get("risk_breakdown") or {}).get("volatility"),
                "ts": row.get("ts"),
            }
        )
    return out


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), limit: int = 100) -> list[dict[str, Any]]:
    rows = db.execute(
        select(AlertLog, Symbol)
        .join(Symbol, AlertLog.symbol_id == Symbol.id)
        .order_by(desc(AlertLog.ts))
        .limit(limit)
    ).all()
    out: list[dict[str, Any]] = []
    for alert, sym in rows:
        out.append(
            {
                "id": alert.id,
                "market": sym.market,
                "channel": alert.channel,
                "status": alert.status,
                "payload": alert.payload,
                "ts": alert.ts.isoformat() if alert.ts else None,
            }
        )
    return out
