from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FunctionInstance:
    """Represents a function instance with a lifecycle state."""

    instance_id: str
    state: str = "TERMINATED"
    warm_start_time: float | None = None
    created_at: float = 0.0
    idle_since: float | None = None
    current_requests: int = 0
    metadata: dict = field(default_factory=dict)

    def become_warm(self, timestamp: float):
        self.state = "WARM"
        self.warm_start_time = timestamp
        self.idle_since = timestamp

    def become_starting(self, timestamp: float):
        self.state = "STARTING"
        self.created_at = timestamp

    def terminate(self):
        self.state = "TERMINATED"
        self.warm_start_time = None
        self.idle_since = None
        self.current_requests = 0
