from .base import BaseController, ControllerAction, ControllerState

class ThresholdController(BaseController):
    """Prewarm when queued demand reaches a configured threshold."""

    def __init__(self, config=None, threshold=5, prewarm_count=1):
        super().__init__(config)
        self.threshold = threshold
        self.prewarm_count = prewarm_count

    def decide(self, state: ControllerState) -> ControllerAction:
        if state.queue_length >= self.threshold:
            return ControllerAction(
                action="prewarm",
                target_warm_instances=(
                    state.warm_instances + self.prewarm_count
                ),
            )

        return ControllerAction(
            action="maintain_warm_pool",
            target_warm_instances=state.warm_instances,
        )