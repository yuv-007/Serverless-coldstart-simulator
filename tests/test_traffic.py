from Traffic.synthetic import generate_request_trace


def test_uniform_request_trace_is_deterministic():

    trace = generate_request_trace(
        duration_seconds=2,
        rate_per_second=4,
        seed=42,
        arrival_process="uniform",
    )

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


def test_poisson_request_trace_is_reproducible():

    trace_a = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="poisson",
    )

    trace_b = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="poisson",
    )

    assert trace_a.arrivals_ms == trace_b.arrivals_ms


def test_different_poisson_seeds_produce_different_traces():

    trace_a = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="poisson",
    )

    trace_b = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=99,
        arrival_process="poisson",
    )

    assert trace_a.arrivals_ms != trace_b.arrivals_ms


def test_poisson_trace_is_chronologically_ordered():

    trace = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="poisson",
    )

    assert list(trace.arrivals_ms) == sorted(
        trace.arrivals_ms
    )


def test_invalid_arrival_process_is_rejected():

    try:
        generate_request_trace(
            duration_seconds=10,
            rate_per_second=5,
            arrival_process="invalid",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for unsupported arrival process"
        )


def test_negative_rate_is_rejected():

    try:
        generate_request_trace(
            duration_seconds=10,
            rate_per_second=-1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for negative rate"
        )


def test_zero_rate_produces_empty_trace():

    trace = generate_request_trace(
        duration_seconds=10,
        rate_per_second=0,
    )

    assert trace.arrivals_ms == ()

def test_bursty_request_trace_is_reproducible():

    trace_a = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="bursty",
        burst_probability=0.5,
        burst_multiplier=4.0,
        burst_duration_seconds=2,
    )

    trace_b = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="bursty",
        burst_probability=0.5,
        burst_multiplier=4.0,
        burst_duration_seconds=2,
    )

    assert trace_a.arrivals_ms == trace_b.arrivals_ms

def test_different_bursty_seeds_produce_different_traces():

    trace_a = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="bursty",
    )

    trace_b = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=99,
        arrival_process="bursty",
    )

    assert trace_a.arrivals_ms != trace_b.arrivals_ms

def test_bursty_trace_is_chronologically_ordered():

    trace = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        seed=42,
        arrival_process="bursty",
    )

    assert list(trace.arrivals_ms) == sorted(
        trace.arrivals_ms
    )

def test_invalid_burst_probability_is_rejected():

    try:
        generate_request_trace(
            duration_seconds=10,
            rate_per_second=5,
            arrival_process="bursty",
            burst_probability=1.5,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid burst probability"
        )

def test_step_request_trace_is_reproducible():

    trace_a = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        step_rate_per_second=20,
        step_at_seconds=5,
        seed=42,
        arrival_process="step",
    )

    trace_b = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        step_rate_per_second=20,
        step_at_seconds=5,
        seed=42,
        arrival_process="step",
    )

    assert trace_a.arrivals_ms == trace_b.arrivals_ms

def test_step_request_trace_changes_rate():

    trace = generate_request_trace(
        duration_seconds=10,
        rate_per_second=5,
        step_rate_per_second=20,
        step_at_seconds=5,
        seed=42,
        arrival_process="step",
    )

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

def test_step_request_trace_requires_step_parameters():

    try:
        generate_request_trace(
            duration_seconds=10,
            rate_per_second=5,
            arrival_process="step",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError when step parameters are missing"
        )

def test_periodic_request_trace_is_reproducible():

    trace_a = generate_request_trace(
        duration_seconds=8,
        rate_per_second=10,
        periodic_peak_rate_per_second=30,
        periodic_period_seconds=4,
        seed=42,
        arrival_process="periodic",
    )

    trace_b = generate_request_trace(
        duration_seconds=8,
        rate_per_second=10,
        periodic_peak_rate_per_second=30,
        periodic_period_seconds=4,
        seed=42,
        arrival_process="periodic",
    )

    assert trace_a.arrivals_ms == trace_b.arrivals_ms

def test_periodic_request_trace_has_high_and_low_phases():

    trace = generate_request_trace(
        duration_seconds=8,
        rate_per_second=10,
        periodic_peak_rate_per_second=30,
        periodic_period_seconds=4,
        seed=42,
        arrival_process="periodic",
    )

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

def test_periodic_request_trace_requires_periodic_parameters():

    try:
        generate_request_trace(
            duration_seconds=8,
            rate_per_second=10,
            arrival_process="periodic",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError when periodic parameters are missing"
        )

