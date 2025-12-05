"""Additional utilities for pytest-async-benchmark."""

import statistics
from typing import Any


def compare_benchmarks(
    result1: dict[str, Any], result2: dict[str, Any]
) -> dict[str, float]:
    """Compare two benchmark results and return relative performance metrics."""
    return {
        "mean_ratio": result2["mean"] / result1["mean"],
        "min_ratio": result2["min"] / result1["min"],
        "max_ratio": result2["max"] / result1["max"],
        "speedup": result1["mean"] / result2["mean"],
        "relative_stddev": (result2["stddev"] - result1["stddev"]) / result1["stddev"],
    }


def benchmark_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a summary of multiple benchmark results."""
    all_means = [r["mean"] for r in results]
    all_stddevs = [r["stddev"] for r in results]

    return {
        "total_tests": len(results),
        "fastest_mean": min(all_means),
        "slowest_mean": max(all_means),
        "average_mean": statistics.mean(all_means),
        "mean_variation": statistics.stdev(all_means) if len(all_means) > 1 else 0,
        "stability_score": 1
        - (statistics.mean(all_stddevs) / statistics.mean(all_means)),
    }


def performance_grade(result: dict[str, Any], thresholds: dict[str, float]) -> str:
    """Grade performance based on configurable thresholds."""
    mean_time = result["mean"]

    if mean_time <= thresholds.get("excellent", 0.001):
        return "A+"
    elif mean_time <= thresholds.get("good", 0.005):
        return "A"
    elif mean_time <= thresholds.get("acceptable", 0.01):
        return "B"
    elif mean_time <= thresholds.get("slow", 0.05):
        return "C"
    else:
        return "D"
