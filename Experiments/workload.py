from dataclasses import dataclass, field

from Traffic.synthetic import generate_request_trace
from Traffic.trace import TrafficTrace


@dataclass(frozen=True)
class WorkloadSpec:
    """Configuration describing a synthetic workload."""

    duration_seconds: float
    rate_per_second: float
    execution_time_ms: float = 50.0
    seed: int = 42
    arrival_process: str = "uniform"

    burst_probability: float = 0.2
    burst_multiplier: float = 4.0
    burst_duration_seconds: int = 1

    metadata: dict = field(default_factory=dict)

    def generate(self) -> TrafficTrace:
        """Generate the request-level traffic trace."""

        trace = generate_request_trace(
            duration_seconds=self.duration_seconds,
            rate_per_second=self.rate_per_second,
            execution_time_ms=self.execution_time_ms,
            seed=self.seed,
            arrival_process=self.arrival_process,
            burst_probability=self.burst_probability,
            burst_multiplier=self.burst_multiplier,
            burst_duration_seconds=self.burst_duration_seconds,
        )

        return trace