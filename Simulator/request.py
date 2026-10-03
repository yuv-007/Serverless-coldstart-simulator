from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Request:
    """Single incoming request to the serverless system."""

    request_id: str
    arrival_time: float
    execution_time_ms: float = 50.0
    cold_start: bool = False
    latency_ms: float = 0.0
    start_time: float | None = None
    completion_time: float | None = None
    metadata: dict = field(default_factory=dict)

    def mark_completed(self, completion_time: float):
        self.completion_time = completion_time
        self.latency_ms = max(0.0, completion_time - self.arrival_time)
