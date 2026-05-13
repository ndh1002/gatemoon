"""Heuristic rug / manipulation risk from exchange-visible data only."""

from __future__ import annotations

from typing import Any


def compute_risk_score(
    *,
    spread_pct: float,
    volatility_1h: float,
    change_pct_abs: float,
    volume_usdt: float,
    meme_keyword: bool,
    whale_concentration: float,
) -> tuple[float, dict[str, float]]:
    """
    Returns risk 0-100 (higher = riskier) and component breakdown.
    Not on-chain audit — combines liquidity tightness, vol spike, and flow skew.
    """
    spread_component = min(100.0, max(0.0, (spread_pct - 0.02) * 400.0))
    vol_component = min(100.0, volatility_1h * 180.0)
    pump_component = min(100.0, change_pct_abs * 1.2)
    thin_component = min(100.0, max(0.0, 40.0 - (volume_usdt / 5_000_000.0) * 40.0))
    whale_component = min(100.0, whale_concentration * 100.0)
    meme_component = 8.0 if meme_keyword else 0.0

    risk = (
        0.22 * spread_component
        + 0.24 * vol_component
        + 0.18 * pump_component
        + 0.16 * thin_component
        + 0.12 * whale_component
        + 0.08 * meme_component
    )
    risk = float(max(0.0, min(100.0, risk)))
    breakdown = {
        "spread": spread_component,
        "volatility": vol_component,
        "pump_chase": pump_component,
        "thin_liquidity": thin_component,
        "whale_skew": whale_component,
        "meme_factor": meme_component,
    }
    return risk, breakdown
