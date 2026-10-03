from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.no_prewarm import NoPrewarmController
from Controllers.threshold import ThresholdController
from Simulator.config import SimulationConfig
from Simulator.engine import ServerlessSimulator
from Simulator.instance import FunctionInstance
from Simulator.metrics import compute_metrics
from Simulator.request import Request
from Traffic.synthetic import generate_synthetic_trace


def test_function_instance_lifecycle():
    instance = FunctionInstance(instance_id="i-1")
    assert instance.state == "TERMINATED"

    instance.become_starting(10.0)
    assert instance.state == "STARTING"

    instance.become_warm(20.0)
    assert instance.state == "WARM"
    assert instance.warm_start_time == 20.0

    instance.terminate()
    assert instance.state == "TERMINATED"


def test_request_latency_and_cold_start_tracking():
    req = Request(request_id="r-1", arrival_time=10.0, execution_time_ms=50.0, cold_start=True)
    req.mark_completed(25.0)

    assert req.cold_start is True
    assert req.latency_ms == 15.0
    assert req.completion_time == 25.0


def test_synthetic_trace_is_reproducible():
    trace1 = generate_synthetic_trace(duration_seconds=5, rate_per_second=10, seed=7, burstiness=2)
    trace2 = generate_synthetic_trace(duration_seconds=5, rate_per_second=10, seed=7, burstiness=2)
    assert trace1 == trace2
    assert len(trace1) == 5
    assert trace1[0]["rate"] >= 0


def test_metrics_include_percentiles_and_cold_start_rate():
    metrics = compute_metrics([100, 200, 300, 400], cold_starts=2, total_requests=4)
    assert metrics["p50"] > 0
    assert metrics["p95"] > metrics["p50"]
    assert metrics["cold_start_rate"] == 0.5


def test_baseline_simulator_runs_and_reports_summary():
    config = SimulationConfig(duration_seconds=10, seed=3, request_rate_per_second=2, cold_start_time_ms=50)
    sim = ServerlessSimulator(config)
    result = sim.run()

    assert "total_requests" in result
    assert "cold_starts" in result
    assert "metrics" in result
    assert result["total_requests"] >= 0


def test_controllers_expose_expected_actions():
    no_prewarm = NoPrewarmController()
    fixed = FixedWarmPoolController(warm_pool_target=3)
    threshold = ThresholdController(threshold=5)

    state = {"warm_instances": 1, "queue_length": 2}
    assert no_prewarm.decide(state)["action"] == "serve_or_start"
    assert fixed.decide(state)["target_warm_instances"] == 3
    assert threshold.decide({"queue_length": 6})["action"] == "prewarm"


def test_simulator_accepts_controller_and_produces_summary():
    config = SimulationConfig(duration_seconds=10, seed=9, request_rate_per_second=3, cold_start_time_ms=80)
    sim = ServerlessSimulator(config)
    result = sim.run(controller=FixedWarmPoolController(warm_pool_target=2))

    assert "controller" in result
    assert result["controller"] == "FixedWarmPoolController"
    assert "metrics" in result
