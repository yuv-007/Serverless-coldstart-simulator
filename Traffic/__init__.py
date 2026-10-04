from .trace import TrafficTrace
from .synthetic import (
    generate_request_trace,
    generate_synthetic_trace,
)

__all__ = [
    "TrafficTrace",
    "generate_request_trace",
    "generate_synthetic_trace",
]