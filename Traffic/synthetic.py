from __future__ import annotations

import random


def generate_synthetic_trace(duration_seconds: float, rate_per_second: float, seed: int = 42, burstiness: float = 0.0):
    """Create a simple synthetic workload trace for early experiments."""
    rng = random.Random(seed)
    trace = []
    for t in range(int(duration_seconds)):
        base = rate_per_second
        burst = rng.uniform(-burstiness, burstiness) * rate_per_second
        arrival_rate = max(0.0, base + burst)
        arrivals = int(arrival_rate)
        trace.append({"time": t, "rate": arrival_rate, "arrivals": arrivals})
    return trace

from .trace import TrafficTrace
def generate_request_trace(
    duration_seconds: float,
    rate_per_second: float,
    execution_time_ms: float = 50.0,
    seed: int = 42,
) -> TrafficTrace:
    """Generate a deterministic request-level trace for experiments.

    The current generator preserves the simulator's existing evenly-spaced
    request behavior. The important architectural change is that the trace
    is generated once and can then be replayed against multiple controllers.
    """

    request_count = max(
        0,
        int(rate_per_second * duration_seconds),
    )

    if request_count == 0 and rate_per_second > 0:
        request_count = 1

    duration_ms = float(duration_seconds) * 1000.0

    arrivals_ms = tuple(
        (index / max(request_count, 1)) * duration_ms
        for index in range(request_count)
    )

    return TrafficTrace(
        arrivals_ms=arrivals_ms,
        execution_time_ms=execution_time_ms,
        source="synthetic",
        metadata={
            "seed": seed,
            "duration_seconds": duration_seconds,
            "rate_per_second": rate_per_second,
        },
    )