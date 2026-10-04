from .base import Controller


class StaticController(Controller):
    """Maintain a fixed target number of active instances."""

    def __init__(self, config=None, target_instances=2):
        super().__init__(config)
        self.target_instances = target_instances

    def decide(self, state):
        return {
            "action": "maintain_warm_pool",
            "target_warm_instances": self.target_instances,
        }