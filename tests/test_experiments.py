from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.no_prewarm import NoPrewarmController
from Experiments.runner import ExperimentRunner
from Simulator.config import SimulationConfig
from Traffic.synthetic import generate_request_trace
from Experiments.workload import WorkloadSpec

def test_experiment_runner_reuses_identical_traffic_trace():

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=4,
        cold_start_time_ms=300,
        execution_time_ms=50,
    )

    trace = generate_request_trace(
        duration_seconds=2,
        rate_per_second=4,
        execution_time_ms=50,
        seed=123,
    )

    runner = ExperimentRunner(config, trace)

    results = runner.run(
        {
            "no_prewarm": lambda: NoPrewarmController(),
            "fixed": lambda: FixedWarmPoolController(
                warm_pool_target=2
            ),
        }
    )

    assert len(results) == 2

    assert {
        result.total_requests
        for result in results
    } == {8}

    arrival_times = [
        request["arrival_time"]
        for request in results[0].raw_result["requests"]
    ]

    other_arrival_times = [
        request["arrival_time"]
        for request in results[1].raw_result["requests"]
    ]

    assert arrival_times == other_arrival_times


def test_experiment_runner_returns_comparable_rows():

    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=2,
    )

    trace = generate_request_trace(
        duration_seconds=1,
        rate_per_second=2,
        execution_time_ms=50,
    )

    runner = ExperimentRunner(config, trace)

    results = runner.run(
        {
            "no_prewarm": lambda: NoPrewarmController()
        }
    )

    rows = runner.as_rows(results)

    assert len(rows) == 1

    assert rows[0]["controller"] == "no_prewarm"

    assert "p50_ms" in rows[0]
    assert "p95_ms" in rows[0]
    assert "p99_ms" in rows[0]
    assert "cold_start_rate" in rows[0]
    assert "slo_violations" in rows[0]

def test_experiment_runner_can_generate_trace_from_workload():

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=4,
        execution_time_ms=50,
    )

    workload = WorkloadSpec(
        duration_seconds=2,
        rate_per_second=4,
        execution_time_ms=50,
        seed=123,
        arrival_process="uniform",
    )

    runner = ExperimentRunner(
        config,
        workload=workload,
    )

    assert runner.traffic_trace == workload.generate()

def test_experiment_runner_reuses_workload_generated_trace():

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=4,
        cold_start_time_ms=300,
        execution_time_ms=50,
    )

    workload = WorkloadSpec(
        duration_seconds=2,
        rate_per_second=4,
        execution_time_ms=50,
        seed=123,
        arrival_process="uniform",
    )

    runner = ExperimentRunner(
        config,
        workload=workload,
    )

    results = runner.run(
        {
            "no_prewarm": lambda: NoPrewarmController(),
            "fixed": lambda: FixedWarmPoolController(
                warm_pool_target=2
            ),
        }
    )

    assert len(results) == 2

    assert {
        result.total_requests
        for result in results
    } == {8}

    arrival_times = [
        request["arrival_time"]
        for request in results[0].raw_result["requests"]
    ]

    other_arrival_times = [
        request["arrival_time"]
        for request in results[1].raw_result["requests"]
    ]

    assert arrival_times == other_arrival_times

def test_experiment_runner_rejects_trace_and_workload_together():

    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=2,
    )

    trace = generate_request_trace(
        duration_seconds=1,
        rate_per_second=2,
    )

    workload = WorkloadSpec(
        duration_seconds=1,
        rate_per_second=2,
    )

    import pytest

    with pytest.raises(ValueError):
        ExperimentRunner(
            config,
            traffic_trace=trace,
            workload=workload,
        )

def test_experiment_runner_requires_trace_or_workload():

    config = SimulationConfig(
        duration_seconds=1,
        request_rate_per_second=2,
    )

    import pytest

    with pytest.raises(ValueError):
        ExperimentRunner(config)

def test_experiment_result_records_workload_configuration():

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=4,
    )

    workload = WorkloadSpec(
        duration_seconds=2,
        rate_per_second=4,
        seed=123,
        arrival_process="bursty",
        burst_probability=0.5,
        burst_multiplier=3.0,
        burst_duration_seconds=2,
    )

    runner = ExperimentRunner(
        config,
        workload=workload,
    )

    results = runner.run(
        {
            "no_prewarm": lambda: NoPrewarmController(),
        }
    )

    result = results[0]

    assert result.workload_duration_seconds == 2
    assert result.workload_rate_per_second == 4
    assert result.workload_seed == 123
    assert result.workload_arrival_process == "bursty"

def test_experiment_rows_include_workload_configuration():

    config = SimulationConfig(
        duration_seconds=2,
        request_rate_per_second=4,
    )

    workload = WorkloadSpec(
        duration_seconds=2,
        rate_per_second=4,
        seed=99,
        arrival_process="poisson",
    )

    runner = ExperimentRunner(
        config,
        workload=workload,
    )

    results = runner.run(
        {
            "no_prewarm": lambda: NoPrewarmController(),
        }
    )

    rows = runner.as_rows(results)

    row = rows[0]

    assert row["workload_duration_seconds"] == 2
    assert row["workload_rate_per_second"] == 4
    assert row["workload_seed"] == 99
    assert row["workload_arrival_process"] == "poisson"