"""Utility functions for async benchmarking."""

import asyncio


def format_time(seconds: float) -> str:
    """Format time duration in human-readable format."""
    if seconds >= 1.0:
        return f"{seconds:.3f}s"
    elif seconds >= 0.001:
        return f"{seconds * 1000:.3f}ms"
    elif seconds >= 0.000001:
        return f"{seconds * 1000000:.3f}μs"
    else:
        return f"{seconds * 1000000000:.3f}ns"


def validate_async_function(func) -> bool:
    """Validate that a function is async."""
    return asyncio.iscoroutinefunction(func)


def get_event_loop():
    """Get or create an event loop safely."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
