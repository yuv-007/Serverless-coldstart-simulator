class ForecastUncertaintyModel:
    """Simple uncertainty wrapper around a point prediction."""

    def __init__(self, error_margin=0.1):
        self.error_margin = max(0.0, float(error_margin))

    def interval(self, point_prediction):
        value = float(point_prediction)
        return {
            "prediction": value,
            "lower": value * (1 - self.error_margin),
            "upper": value * (1 + self.error_margin),
        }
