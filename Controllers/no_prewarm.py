from .base import BaseController, ControllerAction, ControllerState


class NoPrewarmController(BaseController):
    """Baseline strategy: create instances only when they are needed."""

    def decide(self, state: ControllerState) -> ControllerAction:
        return ControllerAction(
            action="serve_or_start",
            target_warm_instances=state.warm_instances,
        )