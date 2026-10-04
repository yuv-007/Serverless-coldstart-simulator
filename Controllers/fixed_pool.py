from .base import BaseController, ControllerAction, ControllerState


class FixedWarmPoolController(BaseController):
    """Maintain a fixed number of warm instances."""

    def __init__(self, config=None, warm_pool_target=2):
        super().__init__(config)
        self.warm_pool_target = warm_pool_target

    def decide(self, state: ControllerState) -> ControllerAction:
        return ControllerAction(
            action="maintain_warm_pool",
            target_warm_instances=self.warm_pool_target,
        )