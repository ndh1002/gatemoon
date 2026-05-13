"""
Train a small XGBoost regressor on synthetic demo labels and save to models/moonshot_xgb.json.

Replace the synthetic dataset with your own historical features + forward returns for production use.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xgboost as xgb

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


def main() -> None:
    rng = np.random.default_rng(42)
    n = 5000
    x = rng.random((n, len(FEATURE_ORDER)))
    # Synthetic target: weighted sum + noise
    w = np.array([0.18, 0.14, 0.14, 0.16, 0.12, 0.12, 0.08, 0.06])
    y = (x @ w + rng.normal(0, 0.05, size=n)).clip(0, 1)
    dtrain = xgb.DMatrix(x, label=y, feature_names=FEATURE_ORDER)
    params = {
        "objective": "reg:squarederror",
        "max_depth": 4,
        "eta": 0.08,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
    }
    booster = xgb.train(params, dtrain, num_boost_round=80)
    out = Path(__file__).resolve().parents[1] / "models" / "moonshot_xgb.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out))
    print("Saved", out)


if __name__ == "__main__":
    main()
