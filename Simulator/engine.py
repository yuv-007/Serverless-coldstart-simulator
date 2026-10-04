from __future__ import annotations
from Controllers.base import ControllerState
from dataclasses import dataclass, field
import heapq
from typing import Any, Callable

from .config import SimulationConfig
from .instance import FunctionInstance
from .metrics import compute_metrics
from .queue import RequestQueue
from .request import Request

REQUEST_ARRIVAL = "request_arrival"
INSTANCE_START_COMPLETE = "instance_start_complete"
REQUEST_COMPLETE = "request_complete"
CONTROLLER_TICK = "controller_tick"

EVENT_PRIORITY = {
CONTROLLER_TICK: 0,
INSTANCE_START_COMPLETE: 1,
REQUEST_ARRIVAL: 2,
REQUEST_COMPLETE: 3,
}


@dataclass(order=True)
class SimulationEvent:
    """A timestamped event in the discrete-event simulation."""

    timestamp: float
    priority: int
    sequence: int
    event_type: str = field(compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)


class SimulatorEngine:
    REQUEST_ARRIVAL = "request_arrival"
    INSTANCE_START_COMPLETE = "instance_start_complete"
    REQUEST_COMPLETE = "request_complete"
    CONTROLLER_TICK = "controller_tick"

    """Priority-queue based discrete-event simulation engine.

    The engine owns simulation time and dispatches events in timestamp order.
    Domain behavior remains in ``ServerlessSimulator`` through registered
    event handlers.
    """

    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()
        self.events: list[SimulationEvent] = []
        self.current_time = 0.0
        self._sequence = 0
        self._handlers: dict[str, Callable[[SimulationEvent], None]] = {}
        self.events_processed = 0

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[SimulationEvent], None],
    ):
        self._handlers[event_type] = handler

    def add_event(
        self,
        timestamp: float,
        event_type: str,
        payload: dict | None = None,
    ):
        if timestamp < self.current_time:
            raise ValueError("Cannot schedule an event in the past")

        self._sequence += 1

        event = SimulationEvent(
            timestamp=float(timestamp),
            priority=EVENT_PRIORITY.get(event_type, 99),
            sequence=self._sequence,
            event_type=event_type,
            payload=payload or {},
        )

        heapq.heappush(self.events, event)

    def run(self):
        """Process events chronologically until the queue is empty."""

        while self.events:
            event = heapq.heappop(self.events)

            self.current_time = event.timestamp

            handler = self._handlers.get(event.event_type)

            if handler is None:
                raise ValueError(
                    f"No handler registered for event type: {event.event_type}"
                )

            handler(event)

            self.events_processed += 1

        return {
            "events_processed": self.events_processed,
            "simulation_time": self.current_time,
        }


class ServerlessSimulator:
    REQUEST_ARRIVAL = REQUEST_ARRIVAL
    INSTANCE_START_COMPLETE = INSTANCE_START_COMPLETE
    REQUEST_COMPLETE = REQUEST_COMPLETE
    CONTROLLER_TICK = CONTROLLER_TICK
    """Discrete-event serverless cold-start simulator.

    Traffic generation is intentionally kept separate from this class.
    The current ``run`` method still creates the project's temporary
    evenly-spaced workload; a later phase will replace this input with
    a proper TrafficTrace.
    """

    
    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()
        self.rng = __import__("random").Random(self.config.seed)
        self.controller = None
        self._reset()

    def _reset(self):
        self.engine = SimulatorEngine(self.config)

        self.instances: dict[str, FunctionInstance] = {}
        self.requests: dict[str, Request] = {}

        self.request_queue = RequestQueue()

        self.cold_starts = 0
        self.instance_counter = 0
        self.current_time_ms = 0.0
        self._request_sequence = 0

        self.engine.register_handler(
            self.REQUEST_ARRIVAL,
            self._on_request_arrival,
        )

        self.engine.register_handler(
            self.INSTANCE_START_COMPLETE,
            self._on_instance_start_complete,
        )

        self.engine.register_handler(
            self.REQUEST_COMPLETE,
            self._on_request_complete,
        )
        self.engine.register_handler(
            self.CONTROLLER_TICK,
            self._on_controller_tick,
        )

    @property
    def total_requests(self) -> int:
        return len(self.requests)

    @property
    def warm_instance_ids(self) -> list[str]:
        return [
            instance_id
            for instance_id, instance in self.instances.items()
            if instance.state == "WARM"
        ]

    def _next_instance_id(self) -> str:
        self.instance_counter += 1
        return f"i-{self.instance_counter}"

    def _create_starting_instance(
        self,
        timestamp_ms: float,
    ) -> FunctionInstance | None:

        active_instances = sum(
            instance.state in {"STARTING", "WARM"}
            for instance in self.instances.values()
        )

        if active_instances >= self.config.max_instances:
            return None

        instance = FunctionInstance(
            instance_id=self._next_instance_id()
        )

        instance.become_starting(timestamp_ms)

        self.instances[instance.instance_id] = instance

        self.engine.add_event(
            timestamp_ms + self.config.cold_start_time_ms,
            self.INSTANCE_START_COMPLETE,
            {
                "instance_id": instance.instance_id,
            },
        )

        return instance

    def _available_instance(self) -> FunctionInstance | None:

        for instance in self.instances.values():

            if instance.state != "WARM":
                continue

            if (
                instance.current_requests
                < self.config.max_concurrency_per_instance
            ):
                return instance

        return None

    def _apply_controller_decision(self, state: dict):

        if self.controller is None:
            return

        decision = self.controller.decide(state) or {}

        if "target_warm_instances" in decision:

            target = max(
                0,
                int(decision["target_warm_instances"]),
            )

            active = sum(
                instance.state in {"STARTING", "WARM"}
                for instance in self.instances.values()
            )

            for _ in range(max(0, target - active)):
                self._create_starting_instance(
                    self.current_time_ms
                )

            return

        if decision.get("action") == "prewarm":

            count = max(
                0,
                int(decision.get("count", 0)),
            )

            for _ in range(count):
                self._create_starting_instance(
                    self.current_time_ms
                )

    def _controller_state(self) -> dict:

        starting = sum(
            instance.state == "STARTING"
            for instance in self.instances.values()
        )

        return {
            "time": self.current_time_ms,
            "warm_instances": len(self.warm_instance_ids),
            "starting_instances": starting,
            "queue_length": len(self.request_queue),
            "request_rate": self.config.request_rate_per_second,
        }

    def _typed_controller_state(self) -> ControllerState:
        """Return the current controller state using the standardized schema."""

        return ControllerState.from_legacy_dict(
            self._controller_state()
        )

    def _start_request(
        self,
        request: Request,
        instance: FunctionInstance,
    ):

        instance.current_requests += 1
        instance.idle_since = None

        request.start_time = self.current_time_ms

        self.engine.add_event(
            self.current_time_ms + request.execution_time_ms,
            self.REQUEST_COMPLETE,
            {
                "request_id": request.request_id,
                "instance_id": instance.instance_id,
            },
        )

    def _on_controller_tick(
        self,
        event: SimulationEvent,
    ):
        """Give the controller a periodic decision opportunity."""

        self.current_time_ms = event.timestamp

        self._apply_controller_decision(
            self._controller_state()
        )

    def _on_request_arrival(
        self,
        event: SimulationEvent,
    ):

        self.current_time_ms = event.timestamp

        request: Request = event.payload["request"]

        self.requests[request.request_id] = request

       
        instance = self._available_instance()

        if instance is not None:
            self._start_request(
                request,
                instance,
            )
            return

        # No warm capacity is immediately available.
        # Queue the request first.
        self.request_queue.enqueue(request)

        # Count instances that are already starting.
        # A starting instance represents capacity that is already
        # being prepared for queued requests.
        starting_instances = sum(
            instance.state == "STARTING"
            for instance in self.instances.values()
        )

        # Only create another instance when the number of queued
        # requests exceeds the number of instances already starting.
        #
        # This allows a burst to scale across multiple instances,
        # while preventing unnecessary duplicate cold starts when
        # an existing prewarm operation can serve the request.
        if len(self.request_queue) > starting_instances:

            instance = self._create_starting_instance(
                self.current_time_ms
            )

            if instance is not None:
                request.cold_start = True
                self.cold_starts += 1 
                
                         
    def _on_instance_start_complete(
        self,
        event: SimulationEvent,
    ):

        self.current_time_ms = event.timestamp

        instance_id = event.payload["instance_id"]

        instance = self.instances[instance_id]

        if instance.state != "STARTING":
            return

        instance.become_warm(
            self.current_time_ms
        )

        # If a request is waiting, the newly warm
        # instance immediately serves it.
        request = self.request_queue.dequeue()

        if request is not None:
            self._start_request(
                request,
                instance,
            )

    def _on_request_complete(
        self,
        event: SimulationEvent,
    ):

        self.current_time_ms = event.timestamp

        request = self.requests[
            event.payload["request_id"]
        ]

        instance = self.instances[
            event.payload["instance_id"]
        ]

        request.mark_completed(
            self.current_time_ms
        )

        instance.current_requests = max(
            0,
            instance.current_requests - 1,
        )

        if instance.current_requests == 0:
            instance.idle_since = self.current_time_ms

        # A completion can free capacity for
        # a queued request.
        queued_request = self.request_queue.dequeue()

        if queued_request is not None:

            available = self._available_instance()

            if available is not None:

                self._start_request(
                    queued_request,
                    available,
                )

            else:

                self.request_queue.enqueue(
                    queued_request
                )
    def _schedule_controller_ticks(self):
        """Schedule periodic controller decision events."""

        interval_ms = (
            self.config.controller_interval_seconds * 1000.0
        )

        if interval_ms <= 0:
            return

        simulation_duration_ms = (
            self.config.duration_seconds * 1000.0
        )

        timestamp_ms = interval_ms

        while timestamp_ms <= simulation_duration_ms:
            self.engine.add_event(
                timestamp_ms,
                self.CONTROLLER_TICK,
            )

            timestamp_ms += interval_ms
            
    def _schedule_requests(self):
        """Temporary workload adapter.

        This intentionally remains here for now.
        It will be replaced by TrafficTrace integration
        in the next phase.
        """

        duration_ms = int(
            self.config.duration_seconds * 1000
        )

        request_count = max(
            0,
            int(
                self.config.request_rate_per_second
                * self.config.duration_seconds
            ),
        )

        if (
            request_count == 0
            and self.config.request_rate_per_second > 0
        ):
            request_count = 1

        for index in range(request_count):

            arrival_time_ms = (
                index
                / max(request_count, 1)
            ) * duration_ms

            request = Request(
                request_id=f"r-{index + 1}",
                arrival_time=float(arrival_time_ms),
                execution_time_ms=self.config.execution_time_ms,
            )

            self.engine.add_event(
                arrival_time_ms,
                self.REQUEST_ARRIVAL,
                {
                    "request": request,
                },
            )

    def run(self, controller=None):
        """Run the event-driven simulation and compute metrics."""

        self._reset()

        self.controller = controller

        self._schedule_requests()
        self._schedule_controller_ticks()

        # Give controllers a chance to provision
        # instances before traffic begins.
        self.current_time_ms = 0.0

        self._apply_controller_decision(
            self._controller_state()
        )

        self.engine.run()

        request_list = list(
            self.requests.values()
        )

        latencies = [
            req.latency_ms
            for req in request_list
            if req.completion_time is not None
        ]

        metrics = compute_metrics(
            latencies,
            cold_starts=self.cold_starts,
            total_requests=self.total_requests,
        )

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
                    "start_time": req.start_time,
                    "completion_time": req.completion_time,
                    "cold_start": req.cold_start,
                    "latency_ms": req.latency_ms,
                }
                for req in request_list
            ],
            "events_processed": self.engine.events_processed,
            "simulation_time_ms": self.engine.current_time,
        }

        if controller is not None:
            result["controller"] = (
                controller.__class__.__name__
            )

        return result
