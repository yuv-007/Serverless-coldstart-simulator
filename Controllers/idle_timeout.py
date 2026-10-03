from .base import Controller


class IdleTimeoutController(Controller):
    """A simple idle-timeout controller for warm capacity eviction."""

    def __init__(self, config=None, idle_timeout_seconds=60.0):
        super().__init__(config)
        self.idle_timeout_seconds = idle_timeout_seconds

    def decide(self, state):
        return {
            "action": "evict_if_idle",
            "idle_timeout_seconds": self.idle_timeout_seconds,
        }
