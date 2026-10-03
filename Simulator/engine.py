from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import SimulationConfig
from .instance import FunctionInstance
from .metrics import compute_metrics
from .request import Request


@dataclass
class SimulationEvent:
    """Simple event placeholder used to drive a discrete-event simulator."""

    timestamp: float
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


class SimulatorEngine:
    """Minimal event queue structure for the simulator."""

    def __init__(self, config=None):
        self.config = config or SimulationConfig()
        self.events: list[SimulationEvent] = []

    def add_event(self, timestamp: float, event_type: str, payload: dict | None = None):
        self.events.append(SimulationEvent(timestamp=timestamp, event_type=event_type, payload=payload or {}))

    def run(self):
        """Run the event queue in time order."""
        for event in sorted(self.events, key=lambda e: e.timestamp):
            _ = event
        return {"events_processed": len(self.events)}


class ServerlessSimulator:
    """Minimal simulation loop for request arrivals, cold starts, and baseline policy comparison."""

    def __init__(self, config=None):
        self.config = config or SimulationConfig()
        self.rng = __import__("random").Random(self.config.seed)
        self.instances: dict[str, FunctionInstance] = {}
        self.warm_instance_ids: list[str] = []
        self.requests: list[Request] = []
        self.total_requests = 0
        self.cold_starts = 0
        self.instance_counter = 0
        self.current_time_ms = 0.0
        self.controller = None

    def _next_instance_id(self) -> str:
        self.instance_counter += 1
        return f"i-{self.instance_counter}"

    def _add_warm_instance(self, timestamp_ms: float):
        instance = FunctionInstance(instance_id=self._next_instance_id())
        instance.become_warm(timestamp_ms)
        self.instances[instance.instance_id] = instance
        self.warm_instance_ids.append(instance.instance_id)

    def _apply_controller_decision(self, state: dict):
        if self.controller is None:
            return

        decision = self.controller.decide(state)
        action = decision.get("action")

        if "target_warm_instances" in decision:
            target = int(decision["target_warm_instances"])
            while len(self.warm_instance_ids) < target:
                self._add_warm_instance(self.current_time_ms)
            return

        if action == "prewarm":
            count = int(decision.get("count", 0))
            for _ in range(count):
                self._add_warm_instance(self.current_time_ms)

    def _handle_request(self, arrival_time_ms: float):
        self.current_time_ms = arrival_time_ms
        state = {
            "warm_instances": len(self.warm_instance_ids),
            "queue_length": max(0, self.total_requests - len(self.warm_instance_ids)),
        }
        self._apply_controller_decision(state)

        request = Request(
            request_id=f"r-{self.total_requests + 1}",
            arrival_time=arrival_time_ms,
            execution_time_ms=self.config.execution_time_ms,
        )

        if not self.warm_instance_ids:
            instance = FunctionInstance(instance_id=self._next_instance_id())
            instance.become_starting(arrival_time_ms)
            self.instances[instance.instance_id] = instance
            request.cold_start = True
            request.start_time = arrival_time_ms + self.config.cold_start_time_ms
            completion_time = request.start_time + self.config.execution_time_ms
            request.mark_completed(completion_time)
            instance.become_warm(request.start_time)
            self.warm_instance_ids.append(instance.instance_id)
            self.cold_starts += 1
        else:
            request.start_time = arrival_time_ms
            completion_time = arrival_time_ms + self.config.execution_time_ms
            request.mark_completed(completion_time)

        self.requests.append(request)
        self.total_requests += 1

    def run(self, controller=None):
        """Generate a simple workload and compute aggregate metrics, optionally using a controller."""
        self.controller = controller
        duration_ms = int(self.config.duration_seconds * 1000)
        request_count = max(0, int(self.config.request_rate_per_second * self.config.duration_seconds))

        if request_count == 0:
            request_count = 1 if self.config.request_rate_per_second > 0 else 0

        for index in range(request_count):
            arrival_time_ms = int((index / max(request_count, 1)) * duration_ms)
            self._handle_request(float(arrival_time_ms))

        latencies = [req.latency_ms for req in self.requests]
        metrics = compute_metrics(latencies, cold_starts=self.cold_starts, total_requests=self.total_requests)

        result = {
            "total_requests": self.total_requests,
            "cold_starts": self.cold_starts,
            "warm_instances": len(self.warm_instance_ids),
            "metrics": metrics,
            "cold_start_rate": metrics["cold_start_rate"],
            "requests": [
                {
                    "request_id": req.request_id,
                    "arrival_time": req.arrival_time,
                    "cold_start": req.cold_start,
                    "latency_ms": req.latency_ms,
                }
                for req in self.requests
            ],
        }

        if controller is not None:
            result["controller"] = controller.__class__.__name__

        return result
