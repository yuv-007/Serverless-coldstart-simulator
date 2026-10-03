from __future__ import annotations

from typing import Iterable


def percentile(values: Iterable[float], p: float) -> float:
    """Return the p-th percentile for a numeric iterable."""
    items = sorted(float(v) for v in values)
    if not items:
        return 0.0
    if len(items) == 1:
        return items[0]
    rank = (len(items) - 1) * p
    lo = int(rank)
    hi = min(lo + 1, len(items) - 1)
    fraction = rank - lo
    return items[lo] + (items[hi] - items[lo]) * fraction


def compute_metrics(latencies: list[float], cold_starts: int, total_requests: int) -> dict:
    """Compute a basic set of summary metrics from observed latencies."""
    if not latencies:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "cold_start_rate": 0.0,
            "total_requests": 0,
            "cold_starts": cold_starts,
        }

    return {
        "p50": percentile(latencies, 0.50),
        "p95": percentile(latencies, 0.95),
        "p99": percentile(latencies, 0.99),
        "cold_start_rate": (cold_starts / total_requests) if total_requests else 0.0,
        "total_requests": total_requests,
        "cold_starts": cold_starts,
    }
