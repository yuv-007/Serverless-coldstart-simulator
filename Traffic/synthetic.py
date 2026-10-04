from __future__ import annotations

import random
import math
from .trace import TrafficTrace


def generate_synthetic_trace(
    duration_seconds: float,
    rate_per_second: float,
    burstiness: float = 0.0,
    seed: int = 42,
) -> list[int]:
    """Generate a deterministic per-second request-count trace.

    This function is retained for backward compatibility with the original
    simulator traffic interface.
    """

    rng = random.Random(seed)

    counts: list[int] = []

    for _ in range(int(duration_seconds)):
        base = rate_per_second

        if burstiness > 0:
            base *= rng.uniform(
                1.0 - burstiness,
                1.0 + burstiness,
            )

        counts.append(max(0, int(round(base))))

    return counts

def _poisson_sample(
    rng: random.Random,
    mean: float,
) -> int:
    """Sample a Poisson-distributed integer without external dependencies."""

    if mean <= 0:
        return 0

    limit = math.exp(-mean)
    product = 1.0
    count = 0

    while product > limit:
        count += 1
        product *= rng.random()

    return count - 1

def generate_request_trace(
    duration_seconds: float,
    rate_per_second: float,
    execution_time_ms: float = 50.0,
    seed: int = 42,
    arrival_process: str = "uniform",
    burst_probability: float = 0.2,
    burst_multiplier: float = 4.0,
    burst_duration_seconds: int = 1,
) -> TrafficTrace:
    """Generate a deterministic request-level traffic trace.

    Parameters
    ----------
    duration_seconds:
        Duration of the workload.

    rate_per_second:
        Average request arrival rate.

    execution_time_ms:
        Execution time assigned to every request.

    seed:
        Random seed used by stochastic arrival processes.

    arrival_process:
        Arrival process to use.

        ``"uniform"``
            Evenly spaced arrivals. This preserves the previous behaviour.

        ``"poisson"``
            Stochastic arrivals generated using exponential inter-arrival
            times.

        ``"bursty"``
            Traffic with normal demand interrupted by configurable
            high-intensity bursts.     
    """

    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")

    if rate_per_second < 0:
        raise ValueError("rate_per_second must be non-negative")

    if arrival_process not in {"uniform", "poisson",  "bursty"}:
        raise ValueError(
            f"Unsupported arrival_process: {arrival_process}"
        )
    if not 0.0 <= burst_probability <= 1.0:
        raise ValueError(
            "burst_probability must be between 0 and 1"
        )

    if burst_multiplier < 1.0:
        raise ValueError(
            "burst_multiplier must be at least 1"
        )

    if burst_duration_seconds < 1:
        raise ValueError(
            "burst_duration_seconds must be at least 1"
        )
        
    request_count = int(
        rate_per_second * duration_seconds
    )

    if request_count == 0 and rate_per_second > 0:
        request_count = 1

    duration_ms = float(duration_seconds) * 1000.0

    if request_count == 0:
        arrivals_ms = ()

    elif arrival_process == "uniform":
        arrivals_ms = tuple(
            (index / max(request_count, 1)) * duration_ms
            for index in range(request_count)
        )

    elif arrival_process == "poisson":
        rng = random.Random(seed)

        current_time_ms = 0.0
        arrivals = []

        mean_interarrival_ms = (
            1000.0 / rate_per_second
        )

        for _ in range(request_count):
            interarrival_ms = rng.expovariate(
                1.0 / mean_interarrival_ms
            )

            current_time_ms += interarrival_ms

            if current_time_ms >= duration_ms:
                break

            arrivals.append(current_time_ms)

        arrivals_ms = tuple(arrivals)

    else:
        rng = random.Random(seed)

        arrivals = []
        burst_remaining = 0

        for second in range(int(duration_seconds)):

            if (
                burst_remaining <= 0
                and rng.random() < burst_probability
            ):
                burst_remaining = burst_duration_seconds

            if burst_remaining > 0:
                current_rate = (
                    rate_per_second * burst_multiplier
                )
            else:
                current_rate = rate_per_second

            expected_requests = current_rate

            request_count_this_second = _poisson_sample(
                rng,
                expected_requests,
            )

            second_start_ms = second * 1000.0

            for _ in range(request_count_this_second):
                arrival_offset_ms = rng.uniform(
                    0.0,
                    1000.0,
                )

                arrivals.append(
                    second_start_ms + arrival_offset_ms
                )

            if burst_remaining > 0:
                burst_remaining -= 1

        arrivals_ms = tuple(sorted(arrivals))
    return TrafficTrace(
        arrivals_ms=arrivals_ms,
        execution_time_ms=execution_time_ms,
        source="synthetic",
        metadata={
            "seed": seed,
            "duration_seconds": duration_seconds,
            "rate_per_second": rate_per_second,
            "arrival_process": arrival_process,
            "burst_probability": burst_probability,
            "burst_multiplier": burst_multiplier,
            "burst_duration_seconds": burst_duration_seconds,
        },
    )