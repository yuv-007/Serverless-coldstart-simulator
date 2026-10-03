from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationEvent:
    """Simple event placeholder used to drive a discrete-event simulator."""

    timestamp: float
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


class SimulatorEngine:
    """Minimal placeholder for the project’s discrete-event core."""

    def __init__(self, config=None):
        self.config = config
        self.events = []

    def add_event(self, timestamp: float, event_type: str, payload: dict | None = None):
        self.events.append(SimulationEvent(timestamp=timestamp, event_type=event_type, payload=payload or {}))

    def run(self):
        """Run the event queue in time order."""
        for event in sorted(self.events, key=lambda e: e.timestamp):
            _ = event
        return {"events_processed": len(self.events)}
