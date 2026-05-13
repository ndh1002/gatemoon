"""Whale activity proxy from recent public trades."""

from __future__ import annotations


def whale_metrics(trades: list[dict]) -> tuple[float, float]:
    """
    Returns (whale_score 0-1, concentration 0-1 top decile volume share).
    """
    if not trades:
        return 0.0, 0.0
    amounts: list[float] = []
    for t in trades:
        try:
            cost = abs(float(t.get("cost") or 0.0))
            if cost <= 0 and t.get("amount") and t.get("price"):
                cost = abs(float(t["amount"]) * float(t["price"]))
            amounts.append(cost)
        except (TypeError, ValueError):
            continue
    if not amounts:
        return 0.0, 0.0
    total = sum(amounts)
    if total <= 0:
        return 0.0, 0.0
    amounts_sorted = sorted(amounts, reverse=True)
    k = max(1, len(amounts_sorted) // 10)
    top_sum = sum(amounts_sorted[:k])
    concentration = min(1.0, top_sum / total)
    median = amounts_sorted[len(amounts_sorted) // 2]
    whale_score = min(1.0, (top_sum / max(median, 1e-9)) / (len(amounts_sorted) * 1.8))
    return float(whale_score), float(concentration)
