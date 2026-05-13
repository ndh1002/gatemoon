"""Telegram alert delivery."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import AlertLog, Symbol


def _should_alert(
    db: Session,
    *,
    symbol_market: str,
    moonshot: float,
    risk: float,
) -> tuple[bool, int | None]:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False, None
    if moonshot < settings.telegram_min_moonshot_score:
        return False, None
    if risk > settings.telegram_max_risk_score:
        return False, None

    sym = db.execute(select(Symbol).where(Symbol.market == symbol_market)).scalar_one_or_none()
    if sym is None:
        return False, None

    since = datetime.now(timezone.utc) - timedelta(minutes=settings.telegram_cooldown_minutes)
    recent = db.execute(
        select(AlertLog.id)
        .where(AlertLog.symbol_id == sym.id, AlertLog.ts >= since, AlertLog.channel == "telegram")
        .limit(1)
    ).scalar_one_or_none()
    if recent is not None:
        return False, None
    return True, sym.id


def _log_alert(db: Session, symbol_id: int, text: str, status: str) -> None:
    db.add(
        AlertLog(
            symbol_id=symbol_id,
            channel="telegram",
            payload=text,
            status=status,
        )
    )
    db.commit()


async def maybe_send_alert(
    session_factory: sessionmaker[Session],
    *,
    symbol_market: str,
    moonshot: float,
    risk: float,
    confidence: float,
    details: dict,
) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    with session_factory() as db:
        ok, sym_id = _should_alert(
            db,
            symbol_market=symbol_market,
            moonshot=moonshot,
            risk=risk,
        )
    if not ok or sym_id is None:
        return

    text = (
        f"🌙 *Gate MoonHunter AI*\n"
        f"`{symbol_market}`\n"
        f"Moonshot: *{moonshot:.1f}* | Risk: *{risk:.1f}* | Conf: *{confidence:.1f}*\n"
        f"Vol spike: {details.get('volume_spike')} | Breakout: {details.get('momentum_breakout')}\n"
        f"Whales: {details.get('whale_activity')} | Smart $: {details.get('smart_money')}"
    )
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    status = "failed"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
        status = "sent"
    except (httpx.HTTPError, ValueError):
        pass

    with session_factory() as db:
        try:
            _log_alert(db, sym_id, text, status)
        except Exception:
            db.rollback()
