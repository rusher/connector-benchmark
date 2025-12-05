"""Core pytest plugin for async benchmarking."""

import asyncio
from collections.abc import Awaitable
from typing import Any, Callable, Optional

import pytest
from rich.console import Console
from rich.table import Table

from .display import format_time
from .runner import AsyncBenchmarkRunner


def _is_pytest_asyncio_available() -> bool:
    """Check if pytest-asyncio is available and active."""
    try:
        import pytest_asyncio  # noqa: F401

        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    except ImportError:
        return False


class _SyncResultWrapper:
    """Wrapper that provides sync interface when pytest-asyncio not available."""

    def __init__(self, coro: Awaitable[Any]):
        self._coro = coro
        self._result: dict[str, Any] = {}
        self._run()

    def _run(self):
        """Run the coroutine in a new event loop."""
        try:
            asyncio.get_running_loop()
            raise RuntimeError("Unexpected: event loop already running")
        except RuntimeError:
            self._result = asyncio.run(self._coro)  # type: ignore

    def __getattr__(self, name):
        """Delegate attribute access to the result."""
        return getattr(self._result, name)

    def __getitem__(self, key):
        """Delegate item access to the result."""
        return self._result[key]

    def __setitem__(self, key, value):
        """Delegate item setting to the result."""
        self._result[key] = value

    def __contains__(self, key):
        """Delegate containment check to the result."""
        return key in self._result

    def __iter__(self):
        """Delegate iteration to the result."""
        return iter(self._result)

    def __len__(self):
        """Delegate length to the result."""
        return len(self._result)

    def __repr__(self):
        return repr(self._result)

    def __str__(self):
        return str(self._result)

    def keys(self):
        """Delegate keys() to the result."""
        return self._result.keys()

    def values(self):
        """Delegate values() to the result."""
        return self._result.values()

    def items(self):
        """Delegate items() to the result."""
        return self._result.items()

    def get(self, key, default=None):
        """Delegate get() to the result."""
        return self._result.get(key, default)


class AsyncBenchmarkFixture:
    """Fixture for benchmarking async functions."""

    def __init__(self, request: pytest.FixtureRequest):
        self.request = request
        self.console = Console()
        self.results: dict[str, Any] = {}

    def _get_marker_params(self):
        """Extract parameters from @pytest.mark.async_benchmark marker."""
        marker = self.request.node.get_closest_marker("async_benchmark")
        if marker:
            return marker.kwargs
        return {}

    def __call__(
        self,
        func: Callable,
        *args,
        rounds: Optional[int] = None,
        iterations: Optional[int] = None,
        warmup_rounds: int = 1,
        **kwargs,
    ) -> Any:
        """Benchmark an async function.

        Returns:
            If pytest-asyncio is available and active: An awaitable that yields benchmark results
            If pytest-asyncio is not available: Benchmark results directly (sync interface)
        """
        if not asyncio.iscoroutinefunction(func):
            raise ValueError("Function must be async (coroutine function)")

        marker_params = self._get_marker_params()

        final_rounds = rounds if rounds is not None else marker_params.get("rounds")
        final_iterations = (
            iterations if iterations is not None else marker_params.get("iterations")
        )
        final_warmup = (
            warmup_rounds
            if warmup_rounds != 1
            else marker_params.get("warmup_rounds", 1)
        )

        runner = AsyncBenchmarkRunner(
            rounds=final_rounds, iterations=final_iterations, warmup_rounds=final_warmup
        )

        # Create the benchmark coroutine
        async def _benchmark():
            result = await runner.run(func, *args, **kwargs)
            test_name = self.request.node.name
            self.results[test_name] = result
            self._display_results(test_name, result)
            return result

        if _is_pytest_asyncio_available():
            return _benchmark()
        else:
            return _SyncResultWrapper(_benchmark())

    def _display_results(self, test_name: str, result: dict[str, Any]):
        """Display benchmark results using rich."""
        table = Table(title=f"🚀 Async Benchmark Results: {test_name}")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Min", format_time(result["min"]))
        table.add_row("Max", format_time(result["max"]))
        table.add_row("Mean", format_time(result["mean"]))
        table.add_row("Median", format_time(result["median"]))
        table.add_row("Std Dev", format_time(result["stddev"]))
        table.add_row("Rounds", str(result["rounds"]))
        table.add_row("Iterations", str(result["iterations"]))

        self.console.print("\n")
        self.console.print(table)
        self.console.print("✅ Benchmark completed successfully!\n")


@pytest.fixture
def async_benchmark(request: pytest.FixtureRequest) -> AsyncBenchmarkFixture:
    """Pytest fixture for async benchmarking."""
    return AsyncBenchmarkFixture(request)


def pytest_configure(config):
    """Configure pytest plugin."""
    config.addinivalue_line(
        "markers",
        "async_benchmark(rounds=None, iterations=None, warmup_rounds=1): mark test as an async benchmark with parameters",
    )
