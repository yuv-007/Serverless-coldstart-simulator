from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from Controllers.base import Controller
from Simulator.config import SimulationConfig
from Simulator.engine import ServerlessSimulator
from Traffic.trace import TrafficTrace
from .workload import WorkloadSpec
from .results import ExperimentResult


ControllerFactory = Callable[[], Controller]


class ExperimentRunner:
    """Run multiple controllers against exactly the same traffic trace."""

    def __init__(
        self,
        config: SimulationConfig,
        traffic_trace: TrafficTrace | None = None,
        workload: WorkloadSpec | None = None,
    ):
        self.config = config

        if traffic_trace is not None and workload is not None:
            raise ValueError(
                "Provide either traffic_trace or workload, not both"
            )

        if traffic_trace is None and workload is None:
            raise ValueError(
                "Either traffic_trace or workload must be provided"
            )

        self.workload = workload

        if traffic_trace is not None:
            self.traffic_trace = traffic_trace
        else:
            self.traffic_trace = workload.generate()
            
    def run(
        self,
        controllers: Mapping[
            str,
            ControllerFactory | Controller,
        ],
    ) -> list[ExperimentResult]:

        results: list[ExperimentResult] = []

        for name, controller_or_factory in controllers.items():

            controller = (
                controller_or_factory()
                if callable(controller_or_factory)
                else controller_or_factory
            )

            simulator = ServerlessSimulator(self.config)

            result = simulator.run(
                controller=controller,
                traffic_trace=self.traffic_trace,
            )

            results.append(
                ExperimentResult.from_simulation(
                    name,
                    result,
                )
            )

        return results

    @staticmethod
    def as_rows(
        results: Sequence[ExperimentResult],
    ) -> list[dict]:

        return [
            {
                "controller": result.controller_name,
                "total_requests": result.total_requests,
                "cold_starts": result.cold_starts,
                "cold_start_rate": result.cold_start_rate,
                "p50_ms": result.p50_ms,
                "p95_ms": result.p95_ms,
                "p99_ms": result.p99_ms,
                "slo_violations": result.slo_violations,
            }
            for result in results
        ]