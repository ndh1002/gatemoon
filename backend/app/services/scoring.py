"""Moonshot scoring: feature engineering + optional XGBoost model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover
    xgb = None

FEATURE_ORDER = [
    "volume_spike",
    "volatility",
    "liquidity_inflow",
    "momentum_breakout",
    "trend_strength",
    "whale_activity",
    "social_velocity",
    "smart_money",
]

_WEIGHTS_DEFAULT = np.array([0.18, 0.14, 0.14, 0.16, 0.12, 0.12, 0.08, 0.06], dtype=np.float64)


def _model_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "models" / "moonshot_xgb.json"


def _load_booster() -> Any | None:
    path = _model_path()
    if xgb is None or not path.is_file():
        return None
    booster = xgb.Booster()
    booster.load_model(str(path))
    return booster


def ohlcv_features(ohlcv: list[list[float]]) -> dict[str, float]:
    """ohlcv rows: [ts, o, h, l, c, v]"""
    if len(ohlcv) < 8:
        return {
            "volatility": 0.0,
            "momentum_breakout": 0.0,
            "trend_strength": 0.0,
            "liquidity_inflow": 0.0,
        }
    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    closes = df["close"].astype(float)
    rets = closes.pct_change().dropna()
    volatility = float(np.clip(rets.std() * 12.0, 0.0, 1.0))

    last = float(closes.iloc[-1])
    high_24 = float(df["high"].tail(24).max()) if len(df) >= 2 else last
    low_24 = float(df["low"].tail(24).min()) if len(df) >= 2 else last
    rng = max(high_24 - low_24, 1e-12)
    momentum_breakout = float(np.clip((last - low_24) / rng, 0.0, 1.0))

    x = np.arange(len(closes))
    y = closes.values
    slope = float(np.polyfit(x, y, 1)[0]) if len(y) > 2 else 0.0
    trend_strength = float(np.clip(abs(slope) / (np.mean(np.abs(y)) + 1e-9) * 8.0, 0.0, 1.0))

    vol = df["volume"].astype(float)
    vol_ma = float(vol.rolling(6).mean().iloc[-1] or 0.0)
    vol_last = float(vol.iloc[-1])
    liquidity_inflow = float(np.clip(vol_last / (vol_ma + 1e-9) - 1.0, 0.0, 2.0))
    liquidity_inflow = float(np.clip(liquidity_inflow / 2.0, 0.0, 1.0))

    return {
        "volatility": volatility,
        "momentum_breakout": momentum_breakout,
        "trend_strength": trend_strength,
        "liquidity_inflow": liquidity_inflow,
    }


def volume_spike_score(current_quote_vol: float, history: list[float]) -> float:
    if not history or current_quote_vol <= 0:
        return 0.0
    arr = np.array(history, dtype=np.float64)
    med = float(np.median(arr)) + 1e-9
    ratio = current_quote_vol / med
    return float(np.clip((ratio - 1.0) / 2.5, 0.0, 1.0))


def smart_money_score(trades: list[dict]) -> float:
    if not trades:
        return 0.0
    buy = 0.0
    sell = 0.0
    for t in trades:
        side = (t.get("side") or "").lower()
        try:
            cost = abs(float(t.get("cost") or 0.0))
            if cost <= 0 and t.get("amount") and t.get("price"):
                cost = abs(float(t["amount"]) * float(t["price"]))
        except (TypeError, ValueError):
            continue
        if side == "buy":
            buy += cost
        elif side == "sell":
            sell += cost
    tot = buy + sell
    if tot <= 0:
        return 0.0
    imbalance = (buy - sell) / tot
    return float(np.clip(0.5 + 0.5 * imbalance, 0.0, 1.0))


def assemble_feature_vector(parts: dict[str, float]) -> np.ndarray:
    vec = np.array([float(parts[k]) for k in FEATURE_ORDER], dtype=np.float64).reshape(1, -1)
    return vec


def ensemble_score(vec: np.ndarray) -> float:
    scaler = RobustScaler()
    v = scaler.fit_transform(vec)
    v = np.clip(v, -3.0, 3.0)
    s = float(np.dot(v.flatten(), _WEIGHTS_DEFAULT))
    s = (s + 3.0) / 6.0
    return float(np.clip(s, 0.0, 1.0))


def xgboost_score(booster: Any, vec: np.ndarray) -> float:
    d = xgb.DMatrix(vec, feature_names=FEATURE_ORDER)
    pred = booster.predict(d)
    val = float(np.array(pred).reshape(-1)[0])
    if val > 1.0 or val < 0.0:
        val = 1.0 / (1.0 + np.exp(-val))
    return float(np.clip(val, 0.0, 1.0))


def compute_scores(
    *,
    ticker: dict[str, Any],
    ohlcv: list[list[float]],
    trades: list[dict],
    quote_volume_history: list[float],
    social_velocity: float,
    whale_score: float,
    risk_score: float,
) -> dict[str, Any]:
    ohlc_parts = ohlcv_features(ohlcv)
    qv = 0.0
    try:
        qv = float(ticker.get("quoteVolume") or ticker.get("info", {}).get("quote_volume") or 0.0)
    except (TypeError, ValueError):
        qv = 0.0
    vol_spike = volume_spike_score(qv, quote_volume_history)
    smart = smart_money_score(trades)

    parts = {
        "volume_spike": vol_spike,
        "volatility": ohlc_parts["volatility"],
        "liquidity_inflow": ohlc_parts["liquidity_inflow"],
        "momentum_breakout": ohlc_parts["momentum_breakout"],
        "trend_strength": ohlc_parts["trend_strength"],
        "whale_activity": whale_score,
        "social_velocity": float(np.clip(social_velocity, 0.0, 1.0)),
        "smart_money": smart,
    }
    vec = assemble_feature_vector(parts)
    booster = _load_booster()
    if booster is not None:
        raw = xgboost_score(booster, vec)
        model_label = "xgboost"
    else:
        raw = ensemble_score(vec)
        model_label = "ensemble"

    moonshot = float(np.clip(raw * 100.0, 0.0, 100.0))
    feature_stability = 1.0 - float(np.std(vec)) / (np.mean(np.abs(vec)) + 1e-6)
    confidence = float(np.clip(55.0 + 35.0 * np.clip(feature_stability, 0.0, 1.0) - risk_score * 0.25, 15.0, 95.0))

    breakdown = {k: round(float(parts[k]) * 100.0, 2) for k in FEATURE_ORDER}
    breakdown["model"] = model_label
    breakdown["risk_score"] = round(risk_score, 2)

    return {
        "moonshot_score": round(moonshot, 2),
        "confidence": round(confidence, 2),
        "risk_score": round(risk_score, 2),
        "details": breakdown,
        "raw_model_score": round(raw * 100.0, 4),
    }
