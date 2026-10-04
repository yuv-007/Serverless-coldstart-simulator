from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ControllerState:
    """Observable state presented to a scaling controller."""

    time_ms: float
    warm_instances: int
    starting_instances: int
    queue_length: int
    active_requests: int
    request_rate: float
    @classmethod
    def from_legacy_dict(cls, state: dict) -> "ControllerState":
        """Convert the simulator's legacy state dictionary."""

        return cls(
            time_ms=float(state.get("time", 0.0)),
            warm_instances=int(state.get("warm_instances", 0)),
            starting_instances=int(state.get("starting_instances", 0)),
            queue_length=int(state.get("queue_length", 0)),
            active_requests=int(state.get("active_requests", 0)),
            request_rate=float(state.get("request_rate", 0.0)),
        )


@dataclass(frozen=True)
class ControllerAction:
    """Action returned by a scaling controller."""

    action: str
    target_warm_instances: int | None = None
    metadata: dict = field(default_factory=dict)

class Controller(ABC):
    """Backward-compatible base interface for existing controllers."""

    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def decide(self, state):
        """Return a controller decision."""
        raise NotImplementedError

class BaseController(Controller):
    """Standard controller interface for the new controller architecture."""

    @abstractmethod
    def decide(self, state: ControllerState) -> ControllerAction:
        """Return a scaling action for the current state."""
        raise NotImplementedError