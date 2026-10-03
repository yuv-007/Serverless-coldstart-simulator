from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Simulator.config import SimulationConfig
from Simulator.engine import ServerlessSimulator


def main():
    """Run a minimal baseline experiment and print comparable metrics."""
    config = SimulationConfig(
        duration_seconds=10,
        seed=42,
        request_rate_per_second=2,
        cold_start_time_ms=300,
        execution_time_ms=50,
        warm_pool_target=2,
    )

    simulator = ServerlessSimulator(config)
    result = simulator.run()

    print("Baseline simulation summary")
    print(f"Total requests: {result['total_requests']}")
    print(f"Cold starts: {result['cold_starts']}")
    print(f"Cold start rate: {result['cold_start_rate']:.3f}")
    print(f"P50 latency: {result['metrics']['p50']:.2f} ms")
    print(f"P95 latency: {result['metrics']['p95']:.2f} ms")
    print(f"P99 latency: {result['metrics']['p99']:.2f} ms")


if __name__ == "__main__":
    main()
