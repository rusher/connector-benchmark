"""Core benchmarking logic for async functions."""

import asyncio
import statistics
import time
from typing import Any, Callable, Optional


class AsyncBenchmarkRunner:
    """Runner for async function benchmarks."""

    def __init__(
        self,
        rounds: Optional[int] = None,
        iterations: Optional[int] = None,
        warmup_rounds: int = 1,
    ):
        self.rounds = rounds or 5
        self.iterations = iterations or 1
        self.warmup_rounds = warmup_rounds

    async def run(self, func: Callable, *args, **kwargs) -> dict[str, Any]:
        """Run benchmark for an async function."""
        if not asyncio.iscoroutinefunction(func):
            raise ValueError("Function must be async (coroutine function)")

        for _ in range(self.warmup_rounds):
            await func(*args, **kwargs)

        times: list[float] = []

        for _ in range(self.rounds):
            round_times: list[float] = []

            for _ in range(self.iterations):
                start_time = time.perf_counter()
                await func(*args, **kwargs)
                end_time = time.perf_counter()
                round_times.append(end_time - start_time)

            times.append(statistics.mean(round_times))

        return self._calculate_stats(times)

    def _calculate_stats(self, times: list[float]) -> dict[str, Any]:
        """Calculate statistics from timing data."""
        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stddev": statistics.stdev(times) if len(times) > 1 else 0.0,
            "rounds": self.rounds,
            "iterations": self.iterations,
            "raw_times": times,
        }
