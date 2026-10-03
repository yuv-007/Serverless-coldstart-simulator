from __future__ import annotations


class SimulationEnvironment:
    """Global simulation state visible to controllers and policies."""

    def __init__(self):
        self.time = 0.0
        self.warm_instances = 0
        self.starting_instances = 0
        self.queue_length = 0
        self.total_requests = 0
        self.cold_starts = 0

    def snapshot(self):
        return {
            "time": self.time,
            "warm_instances": self.warm_instances,
            "starting_instances": self.starting_instances,
            "queue_length": self.queue_length,
            "total_requests": self.total_requests,
            "cold_starts": self.cold_starts,
        }
