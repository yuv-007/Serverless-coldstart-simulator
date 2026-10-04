from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrafficTrace:
    """Immutable workload trace shared across experiment runs.

    Each entry in ``arrivals_ms`` represents one request arrival timestamp.
    The trace is independent of any controller or simulator instance so
    multiple policies can be evaluated on identical input.
    """

    arrivals_ms: tuple[float, ...]
    execution_time_ms: float = 50.0
    source: str = "synthetic"
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return max(self.arrivals_ms, default=0.0)