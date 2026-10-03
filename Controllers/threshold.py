from .base import Controller


class ThresholdController(Controller):
    """Reactive threshold-based prewarming policy."""

    def __init__(self, config=None, threshold=5):
        super().__init__(config)
        self.threshold = threshold

    def decide(self, state):
        queue_length = state.get("queue_length", 0)
        if queue_length > self.threshold:
            return {"action": "prewarm", "count": 1}
        return {"action": "maintain", "count": 0}
