from .base import Controller


class NoPrewarmController(Controller):
    """Baseline strategy: create instances only when they are needed."""

    def decide(self, state):
        return {"action": "serve_or_start", "target_warm_instances": state.get("warm_instances", 0)}
