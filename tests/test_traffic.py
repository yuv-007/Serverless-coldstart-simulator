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