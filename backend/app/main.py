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

BAD_COINS = [
    "PEPE",
    "SHIB",
    "FLOKI",
    "DOGE",
    "BONK"
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

            base_symbol = symbol.split("_")[0]

            if base_symbol in BAD_COINS:
                continue

            volume = float(coin.get("volume", 0))

            score = calculate_score(coin)
            volume = float(coin.get("volume", 0))

            if volume < 100000:
                continue

            score = 50

            change = float(coin.get("change", 0))

            if volume > 10_000_000:
                score += 10

            if change > 5:
                score += 20

            if change > 10:
                score += 20

            result.append({
                "symbol": symbol,
                "price": float(coin.get("last", 0)),
                "volume": float(coin.get("volume", 0)),
                "change": float(coin.get("change", 0)),
                "score": score
            })

        result = sorted(result, key=lambda x: x["score"], reverse=True)

        return result

    return app


app = create_app()