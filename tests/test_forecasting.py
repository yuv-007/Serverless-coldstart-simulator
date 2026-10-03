from Controllers.forecast import ForecastController
from Controllers.uncertainty import UncertaintyAwareForecastController
from Forecasting.baseline import MovingAverageForecaster
from Forecasting.uncertainty import ForecastUncertaintyModel


def test_uncertainty_controller_uses_upper_bound_for_prewarm_decision():
    controller = UncertaintyAwareForecastController(prewarm_threshold=11, uncertainty_margin=0.2)
    state = {"warm_instances": 1, "queue_length": 0, "request_rate": 9}
    decision = controller.decide(state)

    assert decision["action"] == "maintain"
    assert "upper_bound" in decision


def test_forecast_controller_issues_prewarm_when_demand_rises():
    controller = ForecastController(window=3, prewarm_threshold=10)
    state = {"warm_instances": 1, "queue_length": 0, "request_rate": 12}
    decision = controller.decide(state)

    assert decision["action"] == "prewarm"
    assert decision["count"] >= 1


def test_moving_average_forecaster_predicts_expected_trend():
    forecaster = MovingAverageForecaster(window=3)
    for value in [10, 20, 30, 40]:
        forecaster.update(value)

    prediction = forecaster.predict(horizon=1)
    assert prediction > 0
    assert prediction >= 30


def test_uncertainty_model_returns_interval_bounds():
    model = ForecastUncertaintyModel(error_margin=0.2)
    interval = model.interval(100)

    assert interval["prediction"] == 100
    assert interval["lower"] < 100
    assert interval["upper"] > 100
