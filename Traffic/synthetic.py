from __future__ import annotations

import random

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


def generate_request_trace(
    duration_seconds: float,
    rate_per_second: float,
    execution_time_ms: float = 50.0,
    seed: int = 42,
    arrival_process: str = "uniform",
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
    """

    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")

    if rate_per_second < 0:
        raise ValueError("rate_per_second must be non-negative")

    if arrival_process not in {"uniform", "poisson"}:
        raise ValueError(
            f"Unsupported arrival_process: {arrival_process}"
        )

    request_count = int(
        rate_per_second * duration_seconds
    )

    if request_count == 0 and rate_per_second > 0:
        request_count = 1

    duration_ms = float(duration_seconds) * 1000.0

    if request_count == 0:
        arrivals_ms: tuple[float, ...] = ()

    elif arrival_process == "uniform":
        arrivals_ms = tuple(
            (index / max(request_count, 1)) * duration_ms
            for index in range(request_count)
        )

    else:
        rng = random.Random(seed)

        current_time_ms = 0.0
        arrivals: list[float] = []

        mean_interarrival_ms = (
            1000.0 / rate_per_second
        )

        for _ in range(request_count):
            interarrival_ms = (
                rng.expovariate(
                    1.0 / mean_interarrival_ms
                )
            )

            current_time_ms += interarrival_ms

            if current_time_ms >= duration_ms:
                break

            arrivals.append(current_time_ms)

        arrivals_ms = tuple(arrivals)

    return TrafficTrace(
        arrivals_ms=arrivals_ms,
        execution_time_ms=execution_time_ms,
        source="synthetic",
        metadata={
            "seed": seed,
            "duration_seconds": duration_seconds,
            "rate_per_second": rate_per_second,
            "arrival_process": arrival_process,
        },
    )