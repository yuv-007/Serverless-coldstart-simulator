from __future__ import annotations

from Controllers.base import (
    BaseController,
    ControllerAction,
    ControllerState,
)
from Forecasting.baseline import MovingAverageForecaster
from Forecasting.uncertainty import ForecastUncertaintyModel


class UncertaintyAwareForecastController(BaseController):
    """Forecast controller that uses an upper prediction bound for prewarming."""

    def __init__(
        self,
        config=None,
        window=5,
        prewarm_threshold=10,
        uncertainty_margin=0.2,
        target_warm_instances=2,
    ):
        super().__init__(config)
        self.window = window
        self.prewarm_threshold = prewarm_threshold
        self.uncertainty_margin = uncertainty_margin
        self.target_warm_instances = target_warm_instances
        self.forecaster = MovingAverageForecaster(window=window)
        self.uncertainty_model = ForecastUncertaintyModel(
            error_margin=uncertainty_margin
        )

    def decide(self, state: ControllerState) -> ControllerAction:
        request_rate = float(state.request_rate)

        self.forecaster.update(request_rate)
        predicted = self.forecaster.predict(horizon=1)

        interval = self.uncertainty_model.interval(predicted)
        upper_bound = interval["upper"]

        metadata = {
            "predicted_demand": predicted,
            "upper_bound": upper_bound,
            "lower_bound": interval["lower"],
        }

        if (
            upper_bound >= self.prewarm_threshold
            or request_rate >= self.prewarm_threshold
        ):
            return ControllerAction(
                action="prewarm",
                target_warm_instances=max(
                    state.warm_instances,
                    self.target_warm_instances,
                ),
                metadata=metadata,
            )

        return ControllerAction(
            action="maintain_warm_pool",
            target_warm_instances=state.warm_instances,
            metadata=metadata,
        )