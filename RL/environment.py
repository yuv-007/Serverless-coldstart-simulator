class RLWarmPoolEnvironment:
    """Placeholder environment for later RL-based scheduling work."""

    def __init__(self, config=None):
        self.config = config

    def reset(self):
        return {"warm_instances": 0, "queue_length": 0}

    def step(self, action):
        return {"warm_instances": 0, "queue_length": 0}, 0.0, False, {}
