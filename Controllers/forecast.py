from __future__ import annotations

from Controllers.base import Controller
from Forecasting.baseline import MovingAverageForecaster


class ForecastController(Controller):
    """Predictive warm-pool controller based on short-horizon demand forecast."""

    def __init__(self, config=None, window=5, prewarm_threshold=10, target_warm_instances=2):
        super().__init__(config)
        self.window = window
        self.prewarm_threshold = prewarm_threshold
        self.target_warm_instances = target_warm_instances
        self.forecaster = MovingAverageForecaster(window=window)

    def decide(self, state):
        request_rate = float(state.get("request_rate", 0.0))
        self.forecaster.update(request_rate)
        predicted = self.forecaster.predict(horizon=1)

        if predicted >= self.prewarm_threshold or request_rate >= self.prewarm_threshold:
            return {
                "action": "prewarm",
                "count": max(1, int(self.target_warm_instances / 2)),
                "predicted_demand": predicted,
            }

        return {
            "action": "maintain",
            "count": 0,
            "predicted_demand": predicted,
        }
