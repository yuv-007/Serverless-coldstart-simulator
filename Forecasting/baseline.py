class MovingAverageForecaster:
    """Simple moving-average model for short-horizon demand prediction."""

    def __init__(self, window=5):
        self.window = max(1, int(window))
        self.history = []

    def update(self, value):
        self.history.append(float(value))
        if len(self.history) > self.window:
            self.history = self.history[-self.window:]

    def predict(self, horizon=1):
        if not self.history:
            return 0.0
        avg = sum(self.history) / len(self.history)
        return avg * max(1, int(horizon))
