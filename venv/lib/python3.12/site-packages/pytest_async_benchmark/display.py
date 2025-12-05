"""Display utilities for async benchmarking."""

from typing import Any, Optional

from rich.console import Console
from rich.table import Table


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


def format_percentage(value: float) -> str:
    """Format percentage with appropriate styling."""
    if value > 0:
        return f"+{value:.1f}%"
    else:
        return f"{value:.1f}%"


def format_speedup(ratio: float) -> str:
    """Format speedup ratio with descriptive text."""
    if ratio > 1:
        return f"{ratio:.2f}x faster"
    elif ratio < 1:
        return f"{1 / ratio:.2f}x slower"
    else:
        return "same speed"


def display_comparison_table(
    comparisons: list[dict[str, Any]],
    title: str = "🚀 Async Benchmark Comparison",
    console: Optional[Console] = None,
) -> None:
    """Display a comparison table for multiple benchmark results."""
    if console is None:
        console = Console()

    table = Table(title=title)

    table.add_column("Metric", style="cyan", no_wrap=True)

    for comp in comparisons:
        name = comp.get("name", "Benchmark")
        table.add_column(name, style="green", justify="right")

    if len(comparisons) == 2:
        table.add_column("Difference", style="yellow", justify="right")

    def get_metric_values(metric: str):
        values = []
        for comp in comparisons:
            result = comp["result"]
            if metric in result:
                values.append(format_time(result[metric]))
            else:
                values.append("N/A")
        return values

    metrics = ["min", "max", "mean", "median", "stddev"]

    for metric in metrics:
        row = [metric.title()]
        row.extend(get_metric_values(metric))

        if len(comparisons) == 2:
            result1 = comparisons[0]["result"]
            result2 = comparisons[1]["result"]

            if metric in result1 and metric in result2:
                val1, val2 = result1[metric], result2[metric]
                if val1 > 0:
                    diff_percent = ((val2 - val1) / val1) * 100
                    speedup = val1 / val2

                    if metric == "mean":
                        row.append(format_speedup(speedup))
                    else:
                        row.append(format_percentage(diff_percent))
                else:
                    row.append("N/A")
            else:
                row.append("N/A")

        table.add_row(*row)

    config_row = ["Rounds"]
    config_row.extend(
        [str(comp["result"].get("rounds", "N/A")) for comp in comparisons]
    )
    if len(comparisons) == 2:
        config_row.append("")
    table.add_row(*config_row)

    iter_row = ["Iterations"]
    iter_row.extend(
        [str(comp["result"].get("iterations", "N/A")) for comp in comparisons]
    )
    if len(comparisons) == 2:
        iter_row.append("")
    table.add_row(*iter_row)

    console.print("\n")
    console.print(table)

    if len(comparisons) == 2:
        result1 = comparisons[0]["result"]
        result2 = comparisons[1]["result"]
        name1 = comparisons[0].get("name", "Version 1")
        name2 = comparisons[1].get("name", "Version 2")

        if "mean" in result1 and "mean" in result2:
            speedup = result1["mean"] / result2["mean"]
            if speedup > 1.1:
                console.print(f"🏆 {name2} is {format_speedup(speedup)} than {name1}")
            elif speedup < 0.9:
                console.print(
                    f"🏆 {name1} is {format_speedup(1 / speedup)} than {name2}"
                )
            else:
                console.print(f"⚖️  {name1} and {name2} have similar performance")

    console.print("✅ Comparison completed successfully!\n")


def validate_async_function(func) -> bool:
    """Validate that a function is async."""
    import asyncio

    return asyncio.iscoroutinefunction(func)


def display_results_rich(benchmark_results, terminalreporter):
    """Display benchmark results using rich."""
    console = Console(file=terminalreporter._tw)

    table = Table(title="Async Benchmark Results 📊")
    table.add_column("Test Case 🧪", style="cyan", no_wrap=True)
    table.add_column("Min (ms)", style="magenta", justify="right")
    table.add_column("Max (ms)", style="magenta", justify="right")
    table.add_column("Mean (ms)", style="green", justify="right")
    table.add_column("StdDev (ms)", style="yellow", justify="right")
    table.add_column("Median (ms)", style="blue", justify="right")
    table.add_column("Rounds 🔁", justify="right")
    table.add_column("Iter/Round 🔄", justify="right")

    for result in benchmark_results:
        status_emoji = "✅"
        table.add_row(
            f"{status_emoji} {result.name}",
            format_time(result.min),
            format_time(result.max),
            format_time(result.mean),
            format_time(result.stddev),
            format_time(result.median),
            str(result.rounds),
            str(result.iterations),
        )

    console.print(table)
