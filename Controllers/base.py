class Controller:
    """Base interface for all scheduling controllers."""

    def __init__(self, config=None):
        self.config = config

    def decide(self, state):
        """Return a controller action given the current simulation state."""
        raise NotImplementedError("Subclasses must implement decide().")
