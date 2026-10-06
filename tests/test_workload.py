from Experiments.workload import WorkloadSpec


def test_workload_spec_generates_uniform_trace():

    workload = WorkloadSpec(
        duration_seconds=2,
        rate_per_second=4,
        seed=42,
        arrival_process="uniform",
    )

    trace = workload.generate()

    assert trace.arrivals_ms == (
        0.0,
        250.0,
        500.0,
        750.0,
        1000.0,
        1250.0,
        1500.0,
        1750.0,
    )


def test_workload_spec_generates_poisson_trace():

    workload = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="poisson",
    )

    trace = workload.generate()

    assert len(trace.arrivals_ms) > 0
    assert list(trace.arrivals_ms) == sorted(trace.arrivals_ms)


def test_workload_spec_generates_bursty_trace():

    workload = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="bursty",
        burst_probability=0.5,
        burst_multiplier=4.0,
        burst_duration_seconds=2,
    )

    trace = workload.generate()

    assert len(trace.arrivals_ms) > 0
    assert list(trace.arrivals_ms) == sorted(trace.arrivals_ms)


def test_workload_spec_is_reproducible():

    workload_a = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        seed=123,
        arrival_process="bursty",
    )

    workload_b = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        seed=123,
        arrival_process="bursty",
    )

    assert (
        workload_a.generate().arrivals_ms
        == workload_b.generate().arrivals_ms
    )


def test_workload_spec_preserves_configuration_metadata():

    workload = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        seed=7,
        arrival_process="poisson",
    )

    trace = workload.generate()

    assert trace.metadata["seed"] == 7
    assert trace.metadata["arrival_process"] == "poisson"
    assert trace.metadata["rate_per_second"] == 5

def test_workload_spec_generates_step_trace():

    workload = WorkloadSpec(
        duration_seconds=10,
        rate_per_second=5,
        step_rate_per_second=20,
        step_at_seconds=5,
        seed=42,
        arrival_process="step",
    )

    trace = workload.generate()

    before_step = [
        arrival
        for arrival in trace.arrivals_ms
        if arrival < 5000
    ]

    after_step = [
        arrival
        for arrival in trace.arrivals_ms
        if arrival >= 5000
    ]

    assert len(before_step) == 25
    assert len(after_step) == 100

def test_workload_spec_generates_periodic_trace():

    workload = WorkloadSpec(
        duration_seconds=8,
        rate_per_second=10,
        periodic_peak_rate_per_second=30,
        periodic_period_seconds=4,
        seed=42,
        arrival_process="periodic",
    )

    trace = workload.generate()

    first_half_cycle = [
        arrival
        for arrival in trace.arrivals_ms
        if 0 <= arrival < 2000
    ]

    second_half_cycle = [
        arrival
        for arrival in trace.arrivals_ms
        if 2000 <= arrival < 4000
    ]

    assert len(first_half_cycle) < len(second_half_cycle)