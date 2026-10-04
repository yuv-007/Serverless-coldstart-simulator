from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerState:
    """Observable state presented to a scaling controller."""

    time_ms: float
    warm_instances: int
    starting_instances: int
    queue_length: int
    active_requests: int
    request_rate: float


@dataclass(frozen=True)
class ControllerAction:
    """Action returned by a scaling controller."""

    action: str
    target_warm_instances: int | None = None

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