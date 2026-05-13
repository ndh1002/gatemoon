from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class MarketHub:
    """In-memory WebSocket fan-out (Redis stores latest snapshot for REST)."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def unregister(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        raw = json.dumps(message, default=str)
        async with self._lock:
            clients = list(self._clients)
        stale: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(raw)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.unregister(ws)
