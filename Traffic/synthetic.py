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
    step_rate_per_second: float | None = None,
    step_at_seconds: float | None = None,
    periodic_peak_rate_per_second: float | None = None,
    periodic_period_seconds: float | None = None,
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

        ``"step"``
            Traffic with a step function arrival process.
    """

    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")

    if rate_per_second < 0:
        raise ValueError("rate_per_second must be non-negative")

    if arrival_process not in {"uniform", "poisson", "bursty", "step", "periodic"}:
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

    if arrival_process == "step":
        if step_rate_per_second is None:
            raise ValueError(
                "step_rate_per_second is required for step traffic"
            )

        if step_rate_per_second < 0:
            raise ValueError(
                "step_rate_per_second must be non-negative"
            )

        if step_at_seconds is None:
            raise ValueError(
                "step_at_seconds is required for step traffic"
            )

        if not 0.0 <= step_at_seconds <= duration_seconds:
            raise ValueError(
                "step_at_seconds must be within the workload duration"
            )

    if arrival_process == "periodic":
        if periodic_peak_rate_per_second is None:
            raise ValueError(
                "periodic_peak_rate_per_second is required for periodic traffic"
            )

        if periodic_peak_rate_per_second < rate_per_second:
            raise ValueError(
                "periodic_peak_rate_per_second must be greater than or equal to rate_per_second"
            )

        if periodic_period_seconds is None:
            raise ValueError(
                "periodic_period_seconds is required for periodic traffic"
            )

        if periodic_period_seconds <= 0:
            raise ValueError(
                "periodic_period_seconds must be positive"
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

    elif arrival_process == "bursty":
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

    elif arrival_process == "step":
        arrivals = []

        step_at_ms = step_at_seconds * 1000.0

        before_duration_ms = min(
            step_at_ms,
            duration_ms,
        )

        before_count = int(
            rate_per_second * before_duration_ms / 1000.0
        )

        after_duration_ms = max(
            0.0,
            duration_ms - step_at_ms,
        )

        after_count = int(
            step_rate_per_second * after_duration_ms / 1000.0
        )

        if before_count > 0 and rate_per_second > 0:
            before_interval_ms = (
                before_duration_ms / before_count
            )

            for index in range(before_count):
                arrivals.append(
                    index * before_interval_ms
                )

        if after_count > 0 and step_rate_per_second > 0:
            after_interval_ms = (
                after_duration_ms / after_count
            )

            for index in range(after_count):
                arrivals.append(
                    step_at_ms + index * after_interval_ms
                )

        arrivals_ms = tuple(arrivals)
    
    elif arrival_process == "periodic":
        arrivals = []

        period_ms = periodic_period_seconds * 1000.0
        half_period_ms = period_ms / 2.0

        current_time_ms = 0.0

        while current_time_ms < duration_ms:

            cycle_position_ms = current_time_ms % period_ms

            if cycle_position_ms < half_period_ms:
                current_rate = rate_per_second
            else:
                current_rate = periodic_peak_rate_per_second

            interval_ms = (
                1000.0 / current_rate
                if current_rate > 0
                else duration_ms
            )

            arrivals.append(current_time_ms)

            current_time_ms += interval_ms

        arrivals_ms = tuple(
            arrival
            for arrival in arrivals
            if arrival < duration_ms
        )

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
            "step_rate_per_second": step_rate_per_second,
            "step_at_seconds": step_at_seconds,
            "periodic_peak_rate_per_second":periodic_peak_rate_per_second,
            "periodic_period_seconds":periodic_period_seconds,
        },
    )