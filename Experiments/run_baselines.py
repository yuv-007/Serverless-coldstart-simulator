from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.forecast import ForecastController
from Controllers.no_prewarm import NoPrewarmController
from Controllers.threshold import ThresholdController
from Simulator.config import SimulationConfig
from Simulator.engine import ServerlessSimulator


def main():
    """Compare multiple baseline controllers on the same workload for fair benchmarking."""
    config = SimulationConfig(
        duration_seconds=10,
        seed=42,
        request_rate_per_second=2,
        cold_start_time_ms=300,
        execution_time_ms=50,
        warm_pool_target=2,
    )

    controllers = [
        ("NoPrewarmController", NoPrewarmController()),
        ("FixedWarmPoolController", FixedWarmPoolController(warm_pool_target=2)),
        ("ThresholdController", ThresholdController(threshold=1)),
        ("ForecastController", ForecastController(window=3, prewarm_threshold=10, target_warm_instances=2)),
    ]

    print("Baseline comparison")
    print("=" * 70)
    for name, controller in controllers:
        simulator = ServerlessSimulator(config)
        result = simulator.run(controller=controller)
        metrics = result["metrics"]
        print(f"{name:<23} | requests={result['total_requests']:>2} | cold_starts={result['cold_starts']:>2} | cold_rate={result['cold_start_rate']:.3f} | p95={metrics['p95']:.2f} ms | p99={metrics['p99']:.2f} ms")


if __name__ == "__main__":
    main()
