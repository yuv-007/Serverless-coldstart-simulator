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
