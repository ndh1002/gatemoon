from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import get_settings
from app.db.models import Base
from app.db.session import get_engine
from app.services.hub import MarketHub
from app.services.scanner import run_scanner
from app.ws.market import router as ws_router
from fastapi import FastAPI
import app.services.gate_ws as gate_ws
from app.ai.moonshot_ai import calculate_score
from app.services.gate_ws import price_history

BAD_WORDS = [
    "5L",
    "5S",
    "3L",
    "3S",
    "BULL",
    "BEAR",
    "DOWN",
    "UP"
]

BAD_COINS = [
    "DOGE5L",
    "BTC5L",
    "ETH5S",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moonhunter")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    hub = MarketHub()
    app.state.hub = hub

    redis_client: redis.Redis | None = None
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis unavailable (%s); continuing without cache.", exc)
        app.state.redis = None
        redis_client = None

    scan_task = asyncio.create_task(run_scanner(hub, redis_client))
    gate_task = asyncio.create_task(gate_ws.gate_loop())
    logger.info("Scanner task started")
    yield
    scan_task.cancel()
    gate_task.cancel()
    try:
        await scan_task
    except asyncio.CancelledError:
        pass
    if redis_client is not None:
        await redis_client.aclose()


def calculate_volume_spike(symbol, current_volume):

    history = gate_ws.volume_history.get(symbol, [])

    if len(history) < 5:
        return 1

    avg_volume = sum(history[:-1]) / max(len(history[:-1]), 1)

    if avg_volume <= 0:
        return 1

    spike = current_volume / avg_volume

    return round(spike, 2)


def calculate_score(coin, volume_spike=1):

    score = 0

    volume = float(coin.get("volume", 0))
    change = float(coin.get("change", 0))

    # volume mạnh
    if volume > 10_000_000:
        score += 20

    if volume > 50_000_000:
        score += 20

    # momentum
    if change > 3:
        score += 20

    if change > 7:
        score += 20

    # volume spike
    if volume_spike > 2:
        score += 20

    if volume_spike > 5:
        score += 20

    return min(score, 100)

def calculate_breakout(symbol, current_price):

    history = price_history.get(symbol, [])

    if len(history) < 10:
        return 0

    recent_high = max(history[:-1])

    if recent_high <= 0:
        return 0

    breakout = (current_price / recent_high) * 100

    return round(breakout, 2)

def create_app():

    settings = get_settings()

    app = FastAPI(
        title="Gate MoonHunter AI",
        version="1.0.0",
        lifespan=lifespan
    )

    app.include_router(api_router)
    app.include_router(ws_router)

    @app.get("/api/debug")
    async def debug():

        return {
            "tracked_count": len(gate_ws.tracked),
            "tracked": gate_ws.tracked
        }

    @app.get("/api/moonshots")
    async def moonshots():

        print("MOONSHOT TRACKED:", gate_ws.tracked)

        result = []

        for symbol, coin in gate_ws.tracked.items():

            # chỉ lấy USDT pairs
            if not symbol.endswith("USDT"):
                continue

            base_symbol = symbol.split("_")[0]

            # lọc leverage token
            if any(x in base_symbol for x in BAD_WORDS):
                continue

            # blacklist coin rác
            if base_symbol in BAD_COINS:
                continue

            # parse data
            volume = float(coin.get("volume", 0))
            volume_spike = calculate_volume_spike(symbol, volume)
            change = float(coin.get("change", 0))
            price = float(coin.get("last", 0))

            # lọc volume thấp
            if volume < 5_000_000:
                continue

            # lọc coin sideway
            if abs(change) < 1:
                continue

            # AI score
            score = calculate_score(coin, volume_spike)
            breakout = calculate_breakout(symbol, price)

            result.append({
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "change": change,
                "score": score,
                "volume_spike": volume_spike,
                "breakout": breakout
            })

        result = sorted(result, key=lambda x: x["score"], reverse=True)

        return result

    return app


app = create_app()