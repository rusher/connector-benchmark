"""Statistics calculation for async benchmarks."""

import statistics
from typing import Any


class StatsContainer:
    """Container for benchmark statistics calculation."""

    def __init__(self):
        self.measurements: list[float] = []

    def add_measurement(self, duration: float):
        """Add a timing measurement."""
        self.measurements.append(duration)

    def calculate_stats(self) -> dict[str, Any]:
        """Calculate comprehensive statistics."""
        if not self.measurements:
            return {}

        return {
            "min": min(self.measurements),
            "max": max(self.measurements),
            "mean": statistics.mean(self.measurements),
            "median": statistics.median(self.measurements),
            "stddev": statistics.stdev(self.measurements)
            if len(self.measurements) > 1
            else 0.0,
            "count": len(self.measurements),
            "raw_times": self.measurements.copy(),
        }

    def reset(self):
        """Reset all measurements."""
        self.measurements.clear()
