from __future__ import annotations

from Controllers.base import (
    BaseController,
    ControllerAction,
    ControllerState,
)
from Forecasting.baseline import MovingAverageForecaster


class ForecastController(BaseController):
    """Predictive warm-pool controller based on short-horizon demand forecast."""

    def __init__(
        self,
        config=None,
        window=5,
        prewarm_threshold=10,
        target_warm_instances=2,
    ):
        super().__init__(config)
        self.window = window
        self.prewarm_threshold = prewarm_threshold
        self.target_warm_instances = target_warm_instances
        self.forecaster = MovingAverageForecaster(window=window)

    def decide(self, state: ControllerState) -> ControllerAction:
        request_rate = float(state.request_rate)

        self.forecaster.update(request_rate)
        predicted = self.forecaster.predict(horizon=1)

        if (
            predicted >= self.prewarm_threshold
            or request_rate >= self.prewarm_threshold
        ):
            target = max(
                state.warm_instances,
                self.target_warm_instances,
            )

            return ControllerAction(
                action="prewarm",
                target_warm_instances=target,
            )

        return ControllerAction(
            action="maintain_warm_pool",
            target_warm_instances=state.warm_instances,
        )