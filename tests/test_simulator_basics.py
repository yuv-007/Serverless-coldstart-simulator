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

def test_engine_processes_events_in_timestamp_order():
    from Simulator.engine import SimulatorEngine

    engine = SimulatorEngine()
    seen = []

    engine.register_handler(
        "probe",
        lambda event: seen.append(event.payload["value"]),
    )

    engine.add_event(
        20.0,
        "probe",
        {"value": 20},
    )

    engine.add_event(
        10.0,
        "probe",
        {"value": 10},
    )

    result = engine.run()

    assert seen == [10, 20]
    assert result["events_processed"] == 2
    assert result["simulation_time"] == 20.0

def test_cold_start_is_modeled_as_elapsed_simulated_time():
    config = SimulationConfig(
        duration_seconds=0.001,
        request_rate_per_second=1000,
        cold_start_time_ms=300,
        execution_time_ms=50,
    )

    simulator = ServerlessSimulator(config)

    result = simulator.run()

    request = result["requests"][0]

    assert request["cold_start"] is True
    assert request["latency_ms"] == 350.0
    assert request["start_time"] == 300.0
    assert request["completion_time"] == 350.0

def test_prewarm_is_completed_before_a_later_request_arrives():
    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=0,
        cold_start_time_ms=300,
        execution_time_ms=50,
    )

    simulator = ServerlessSimulator(config)

    simulator.controller = FixedWarmPoolController(
        warm_pool_target=1
    )

    simulator._apply_controller_decision(
        simulator._controller_state()
    )

    request = Request(
        request_id="r-1",
        arrival_time=500.0,
        execution_time_ms=50.0,
    )

    simulator.engine.add_event(
        500.0,
        simulator.REQUEST_ARRIVAL,
        {"request": request},
    )

    simulator.engine.run()

    observed = simulator.requests["r-1"]

    assert observed.cold_start is False
    assert observed.start_time == 500.0
    assert observed.latency_ms == 50.0

def test_request_arriving_during_prewarm_waits_for_startup():
    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=0,
        cold_start_time_ms=300,
        execution_time_ms=50,
    )

    simulator = ServerlessSimulator(config)

    simulator.controller = FixedWarmPoolController(
        warm_pool_target=1
    )

    simulator._apply_controller_decision(
        simulator._controller_state()
    )

    request = Request(
        request_id="r-1",
        arrival_time=100.0,
        execution_time_ms=50.0,
    )

    simulator.engine.add_event(
        100.0,
        simulator.REQUEST_ARRIVAL,
        {"request": request},
    )

    simulator.engine.run()

    observed = simulator.requests["r-1"]

    assert observed.cold_start is False
    assert observed.start_time == 300.0
    assert observed.latency_ms == 250.0

def test_simultaneous_requests_can_scale_to_multiple_instances():
    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=0,
        cold_start_time_ms=300,
        execution_time_ms=50,
        max_instances=2,
        max_concurrency_per_instance=1,
    )

    simulator = ServerlessSimulator(config)

    requests = [
        Request(
            request_id=f"r-{i}",
            arrival_time=0.0,
            execution_time_ms=50.0,
        )
        for i in range(1, 4)
    ]

    for request in requests:
        simulator.engine.add_event(
            0.0,
            simulator.REQUEST_ARRIVAL,
            {"request": request},
        )

    simulator.engine.run()

    assert len(simulator.instances) == 2
    assert simulator.cold_starts == 2
    assert len(simulator.requests) == 3

def test_excess_requests_are_queued_when_max_instances_are_busy():
    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=0,
        cold_start_time_ms=300,
        execution_time_ms=50,
        max_instances=2,
        max_concurrency_per_instance=1,
    )

    simulator = ServerlessSimulator(config)

    requests = [
        Request(
            request_id=f"r-{i}",
            arrival_time=0.0,
            execution_time_ms=50.0,
        )
        for i in range(1, 4)
    ]

    for request in requests:
        simulator.engine.add_event(
            0.0,
            simulator.REQUEST_ARRIVAL,
            {"request": request},
        )

    simulator.engine.run()

    results = simulator.requests

    assert results["r-1"].start_time == 300.0
    assert results["r-2"].start_time == 300.0
    assert results["r-3"].start_time == 350.0

def test_queued_request_is_not_marked_as_cold_start():
    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=0,
        cold_start_time_ms=300,
        execution_time_ms=50,
        max_instances=2,
        max_concurrency_per_instance=1,
    )

    simulator = ServerlessSimulator(config)

    requests = [
        Request(
            request_id=f"r-{i}",
            arrival_time=0.0,
            execution_time_ms=50.0,
        )
        for i in range(1, 4)
    ]

    for request in requests:
        simulator.engine.add_event(
            0.0,
            simulator.REQUEST_ARRIVAL,
            {"request": request},
        )

    simulator.engine.run()

    results = simulator.requests

    assert results["r-1"].cold_start is True
    assert results["r-2"].cold_start is True
    assert results["r-3"].cold_start is False