from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.no_prewarm import NoPrewarmController
from Controllers.threshold import ThresholdController
from Simulator.config import SimulationConfig
from Simulator.engine import ServerlessSimulator, SimulatorEngine
from Simulator.instance import FunctionInstance
from Simulator.metrics import compute_metrics
from Simulator.request import Request
from Traffic.synthetic import generate_synthetic_trace
from Controllers.static import StaticController
from Controllers.base import (
    BaseController,
    ControllerAction,
    ControllerState,
)
from Controllers.base import ControllerState
from Controllers.forecast import ForecastController


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

    state = {
        "warm_instances": 1,
        "queue_length": 2,
    }

    no_prewarm_action = no_prewarm.decide(
        ControllerState.from_legacy_dict(state)
    )

    assert no_prewarm_action.action == "serve_or_start"
    assert no_prewarm_action.target_warm_instances == 1

    fixed_action = fixed.decide(
        ControllerState.from_legacy_dict(state)
    )

    assert fixed_action.action == "maintain_warm_pool"
    assert fixed_action.target_warm_instances == 3

    threshold_action = threshold.decide(
        ControllerState.from_legacy_dict(
            {"queue_length": 6}
        )
    )

    assert threshold_action.action == "prewarm"
    assert threshold_action.target_warm_instances == 1

    threshold_no_action = threshold.decide(
        ControllerState.from_legacy_dict(
            {
                "queue_length": 2,
                "warm_instances": 3,
            }
        )
    )

    assert threshold_no_action.action == "maintain_warm_pool"
    assert threshold_no_action.target_warm_instances == 3

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

def test_static_controller_maintains_fixed_target():
    controller = StaticController(target_instances=5)

    decision = controller.decide({
        "warm_instances": 1,
        "starting_instances": 0,
        "queue_length": 0,
    })

    assert decision["action"] == "maintain_warm_pool"
    assert decision["target_warm_instances"] == 5

def test_controller_runs_on_periodic_control_ticks():
    class RecordingController:
        def __init__(self):
            self.times = []

        def decide(self, state):
            self.times.append(state["time"])
            return {}

    config = SimulationConfig(
        duration_seconds=3,
        request_rate_per_second=0,
        controller_interval_seconds=1.0,
    )

    controller = RecordingController()
    simulator = ServerlessSimulator(config)

    simulator.run(controller=controller)

    assert controller.times == [
        0.0,
        1000.0,
        2000.0,
        3000.0,
    ]

def test_requests_do_not_trigger_extra_controller_decisions():
    class RecordingController:
        def __init__(self):
            self.times = []

        def decide(self, state):
            self.times.append(state["time"])
            return {}

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=10,
        controller_interval_seconds=1.0,
    )

    controller = RecordingController()
    simulator = ServerlessSimulator(config)

    simulator.run(controller=controller)

    assert controller.times == [
        0.0,
        1000.0,
        2000.0,
    ]
def test_controller_tick_precedes_request_arrival_at_same_timestamp():
    processed = []

    engine = SimulatorEngine()

    engine.register_handler(
        "controller_tick",
        lambda event: processed.append("controller"),
    )

    engine.register_handler(
        "request_arrival",
        lambda event: processed.append("request"),
    )

    engine.add_event(
        1000.0,
        "request_arrival",
        {},
    )

    engine.add_event(
        1000.0,
        "controller_tick",
        {},
    )

    engine.run()

    assert processed == [
        "controller",
        "request",
    ]


def test_controller_state_contains_common_observations():
    state = ControllerState(
        time_ms=1000.0,
        warm_instances=3,
        starting_instances=1,
        queue_length=4,
        active_requests=2,
        request_rate=8.5,
    )

    assert state.time_ms == 1000.0
    assert state.warm_instances == 3
    assert state.starting_instances == 1
    assert state.queue_length == 4
    assert state.active_requests == 2
    assert state.request_rate == 8.5

def test_base_controller_requires_decision_implementation():
    class ExampleController(BaseController):
        def decide(self, state):
            return ControllerAction(
                action="maintain_warm_pool",
                target_warm_instances=2,
            )

    controller = ExampleController()

    state = ControllerState(
        time_ms=0.0,
        warm_instances=2,
        starting_instances=0,
        queue_length=0,
        active_requests=0,
        request_rate=0.0,
    )

    action = controller.decide(state)

    assert action.action == "maintain_warm_pool"
    assert action.target_warm_instances == 2

def test_legacy_controller_state_can_be_converted_to_typed_state():
    legacy_state = {
        "time": 1500.0,
        "warm_instances": 3,
        "starting_instances": 1,
        "queue_length": 4,
        "active_requests": 2,
        "request_rate": 7.5,
    }

    state = ControllerState.from_legacy_dict(legacy_state)

    assert state.time_ms == 1500.0
    assert state.warm_instances == 3
    assert state.starting_instances == 1
    assert state.queue_length == 4
    assert state.active_requests == 2
    assert state.request_rate == 7.5

def test_simulator_can_produce_standardized_controller_state():
    config = SimulationConfig(
        duration_seconds=10,
        request_rate_per_second=2,
    )

    simulator = ServerlessSimulator(config)

    state = simulator._typed_controller_state()

    assert isinstance(state, ControllerState)
    assert state.time_ms == 0.0
    assert state.warm_instances == 0
    assert state.starting_instances == 0
    assert state.queue_length == 0
    assert state.active_requests == 0
    assert state.request_rate == 2.0

def test_controller_state_reports_active_requests():
    config = SimulationConfig(
        duration_seconds=10,
        request_rate_per_second=0,
    )

    simulator = ServerlessSimulator(config)

    instance = simulator._create_starting_instance(0.0)

    assert instance is not None

    instance.state = "WARM"
    instance.current_requests = 3

    state = simulator._controller_state()

    assert state["active_requests"] == 3

def test_migrated_no_prewarm_controller_works_with_simulator():
    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=1,
        controller_interval_seconds=1.0,
    )

    simulator = ServerlessSimulator(config)

    result = simulator.run(
        controller=NoPrewarmController()
    )

    assert result["controller"] == "NoPrewarmController"
    assert result["total_requests"] > 0

def test_migrated_fixed_pool_controller_works_with_simulator():
    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=1,
        controller_interval_seconds=1.0,
    )

    simulator = ServerlessSimulator(config)

    result = simulator.run(
        controller=FixedWarmPoolController(
            warm_pool_target=2
        )
    )

    assert result["controller"] == "FixedWarmPoolController"
    assert result["total_requests"] > 0

def test_migrated_threshold_controller_works_with_simulator():
    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=5,
        controller_interval_seconds=1.0,
    )

    simulator = ServerlessSimulator(config)

    result = simulator.run(
        controller=ThresholdController(
            threshold=1,
            prewarm_count=1,
        )
    )

    assert result["controller"] == "ThresholdController"
    assert result["total_requests"] > 0

def test_migrated_forecast_controller_works_with_simulator():
    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=5,
        controller_interval_seconds=1.0,
    )

    simulator = ServerlessSimulator(config)

    result = simulator.run(
        controller=ForecastController(
            window=3,
            prewarm_threshold=1,
            target_warm_instances=2,
        )
    )

    assert result["controller"] == "ForecastController"
    assert result["total_requests"] > 0