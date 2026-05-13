from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/market")
async def market_socket(websocket: WebSocket) -> None:
    hub = websocket.app.state.hub
    redis = getattr(websocket.app.state, "redis", None)
    await hub.register(websocket)
    if redis is not None:
        try:
            raw = await redis.get("moonhunter:latest_scan")
            if raw:
                await websocket.send_text(raw if isinstance(raw, str) else raw.decode())
        except Exception:
            pass
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=45.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping", "ts": None}))
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unregister(websocket)
