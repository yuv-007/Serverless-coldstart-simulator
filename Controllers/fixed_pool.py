from .base import Controller


class FixedWarmPoolController(Controller):
    """Maintain a fixed number of warm instances."""

    def __init__(self, config=None, warm_pool_target=2):
        super().__init__(config)
        self.warm_pool_target = warm_pool_target

    def decide(self, state):
        return {
            "action": "maintain_warm_pool",
            "target_warm_instances": self.warm_pool_target,
        }
