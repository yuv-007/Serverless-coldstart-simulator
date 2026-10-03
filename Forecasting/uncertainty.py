class ForecastUncertaintyModel:
    """Placeholder for uncertainty-aware forecasting work."""

    def __init__(self, error_margin=0.1):
        self.error_margin = error_margin

    def interval(self, point_prediction):
        return {
            "prediction": point_prediction,
            "lower": point_prediction * (1 - self.error_margin),
            "upper": point_prediction * (1 + self.error_margin),
        }
