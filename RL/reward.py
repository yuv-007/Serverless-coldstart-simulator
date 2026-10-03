class RewardModel:
    """Placeholder for a multi-objective reward function."""

    def __init__(self, latency_weight=1.0, cost_weight=1.0, cold_start_weight=1.0):
        self.latency_weight = latency_weight
        self.cost_weight = cost_weight
        self.cold_start_weight = cold_start_weight

    def compute(self, latency_ms, cost, cold_starts):
        return -(self.latency_weight * latency_ms + self.cost_weight * cost + self.cold_start_weight * cold_starts)
