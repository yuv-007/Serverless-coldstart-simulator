from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentResult:
    """Comparable result from one controller on one workload."""

    controller_name: str
    total_requests: int
    cold_starts: int
    cold_start_rate: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    slo_violations: int
    raw_result: dict

    @classmethod
    def from_simulation(
        cls,
        controller_name: str,
        result: dict,
    ) -> "ExperimentResult":

        metrics = result["metrics"]
        slo_latency_ms = result.get("slo_latency_ms")
        requests = result.get("requests", [])

        if slo_latency_ms is None:
            slo_violations = 0
        else:
            slo_violations = sum(
                request["latency_ms"] > slo_latency_ms
                for request in requests
                if request["completion_time"] is not None
            )

        return cls(
            controller_name=controller_name,
            total_requests=result["total_requests"],
            cold_starts=result["cold_starts"],
            cold_start_rate=result["cold_start_rate"],
            p50_ms=metrics["p50"],
            p95_ms=metrics["p95"],
            p99_ms=metrics["p99"],
            slo_violations=slo_violations,
            raw_result=result,
        )