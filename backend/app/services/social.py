"""Optional social velocity via X API v2 recent search (best-effort)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import get_settings


MEME_KEYWORDS = (
    "DOGE",
    "SHIB",
    "PEPE",
    "FLOKI",
    "BONK",
    "WIF",
    "MEME",
    "MOG",
    "BABY",
    "INU",
    "CAT",
    "FROG",
    "ELON",
    "MOON",
)


def meme_trend_score(symbol_base: str) -> float:
    u = symbol_base.upper()
    hits = sum(1 for k in MEME_KEYWORDS if k in u)
    return min(1.0, 0.15 + hits * 0.22)


async def twitter_mention_velocity(symbol_base: str) -> float | None:
    token = get_settings().twitter_bearer_token
    if not token:
        return None
    query = f"${symbol_base} OR #{symbol_base} min_faves:5 -is:retweet lang:en"
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {token}"}
    params: dict[str, Any] = {"query": query, "max_results": 10}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code != 200:
                return None
            data = r.json()
            meta = data.get("meta", {})
            total = int(meta.get("result_count", 0))
            return min(1.0, total / 10.0)
    except (httpx.HTTPError, ValueError, KeyError):
        return None


async def social_velocity_score(symbol_base: str) -> tuple[float, str]:
    """
    Combined social velocity 0-1 and source label.
    Falls back to neutral when APIs unavailable.
    """
    meme = meme_trend_score(symbol_base)
    try:
        tw = await asyncio.wait_for(twitter_mention_velocity(symbol_base), timeout=9.0)
    except TimeoutError:
        tw = None
    if tw is None:
        return 0.45 + 0.25 * meme, "meme_heuristic"
    return min(1.0, 0.35 * tw + 0.45 * meme + 0.2 * tw * meme), "twitter+meme"
