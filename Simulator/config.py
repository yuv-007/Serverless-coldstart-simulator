from dataclasses import dataclass, field


@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""

    duration_seconds: float = 3600.0
    seed: int = 42
    request_rate_per_second: float = 10.0
    cold_start_time_ms: float = 300.0
    execution_time_ms: float = 50.0
    max_instances: int = 50
    max_concurrency_per_instance: int = 1
    idle_timeout_seconds: float = 60.0
    slo_latency_ms: float = 200.0
    warm_pool_target: int = 2
    burstiness: float = 0.0
    log_enabled: bool = False
    extra: dict = field(default_factory=dict)
