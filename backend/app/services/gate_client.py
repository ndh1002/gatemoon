from __future__ import annotations

import asyncio
from typing import Any

import ccxt.async_support as ccxt

from app.config import get_settings


class GateClient:
    """Async CCXT client for Gate.io spot."""

    def __init__(self) -> None:
        settings = get_settings()
        config: dict[str, Any] = {
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
        if settings.gate_api_key and settings.gate_api_secret:
            config["apiKey"] = settings.gate_api_key
            config["secret"] = settings.gate_api_secret
        self._exchange = ccxt.gateio(config)
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        await self._exchange.close()

    async def fetch_tickers(self) -> dict[str, Any]:
        async with self._lock:
            return await self._exchange.fetch_tickers()

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 48) -> list[list[float]]:
        async with self._lock:
            return await self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    async def fetch_trades(self, symbol: str, limit: int = 120) -> list[dict[str, Any]]:
        async with self._lock:
            return await self._exchange.fetch_trades(symbol, limit=limit)
