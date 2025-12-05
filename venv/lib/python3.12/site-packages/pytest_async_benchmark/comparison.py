"""
Comparison utilities for pytest-async-benchmark.

This module provides high-level utilities for comparing multiple benchmark results
and displaying them in various formats.
"""

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .analytics import compare_benchmarks, performance_grade
from .display import display_comparison_table, format_speedup, format_time
from .runner import AsyncBenchmarkRunner


@dataclass
class BenchmarkScenario:
    """Represents a single benchmark scenario."""

    name: str
    func: Callable[[], Awaitable[Any]]
    rounds: int = 5
    iterations: int = 10
    description: Optional[str] = None


class BenchmarkComparator:
    """High-level utility for comparing multiple benchmarks."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.runner = AsyncBenchmarkRunner()
        self.results: list[dict[str, Any]] = []

    async def add_scenario(
        self,
        name: str,
        func: Callable[[], Awaitable[Any]],
        rounds: int = 5,
        iterations: int = 10,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Add and run a benchmark scenario."""
        scenario = BenchmarkScenario(name, func, rounds, iterations, description)

        self.console.print(f"🏃 Running scenario: [cyan]{name}[/cyan]")
        if description:
            self.console.print(f"   {description}")

        runner = AsyncBenchmarkRunner(rounds=rounds, iterations=iterations)
        result = await runner.run(func)

        scenario_result = {
            "name": name,
            "result": result,
            "description": description,
            "scenario": scenario,
        }

        self.results.append(scenario_result)
        return scenario_result

    def display_all_results(self, title: str = "📊 Benchmark Results Summary"):
        """Display all collected results in a summary table."""
        if not self.results:
            self.console.print("❌ No benchmark results to display")
            return

        display_comparison_table(self.results, title=title, console=self.console)

    def display_pairwise_comparison(
        self, name1: str, name2: str, title: Optional[str] = None
    ):
        """Display a detailed comparison between two specific scenarios."""
        result1 = next((r for r in self.results if r["name"] == name1), None)
        result2 = next((r for r in self.results if r["name"] == name2), None)

        if not result1 or not result2:
            self.console.print(f"❌ Could not find results for '{name1}' or '{name2}'")
            return

        comparison_title = title or f"⚡ {name1} vs {name2}"

        display_comparison_table(
            [result1, result2], title=comparison_title, console=self.console
        )

        comparison = compare_benchmarks(result1["result"], result2["result"])

        self.console.print("\n📈 Detailed Analysis:")
        analysis_text = Text()

        speedup = comparison["speedup"]
        if speedup > 1.2:
            analysis_text.append(f"🚀 {name2} is significantly faster ", style="green")
            analysis_text.append(f"({format_speedup(speedup)})", style="bold green")
        elif speedup < 0.8:
            analysis_text.append(f"🐌 {name1} is significantly faster ", style="red")
            analysis_text.append(f"({format_speedup(1 / speedup)})", style="bold red")
        else:
            analysis_text.append(
                "⚖️  Both scenarios have similar performance", style="yellow"
            )

        self.console.print(Panel(analysis_text, title="Performance Summary"))

    def display_performance_grades(self, thresholds: Optional[dict[str, float]] = None):
        """Display performance grades for all scenarios."""
        if not self.results:
            self.console.print("❌ No results to grade")
            return

        default_thresholds = {
            "excellent": 0.001,
            "good": 0.005,
            "acceptable": 0.01,
            "slow": 0.05,
        }
        thresholds = thresholds or default_thresholds

        from rich.table import Table

        table = Table(title="🏆 Performance Grades")
        table.add_column("Scenario", style="cyan")
        table.add_column("Mean Time", style="yellow", justify="right")
        table.add_column("Grade", style="green", justify="center")
        table.add_column("Status", justify="center")

        for result in self.results:
            grade = performance_grade(result["result"], thresholds)
            mean_time = format_time(result["result"]["mean"])

            status = {"A+": "🏆", "A": "🥇", "B": "🥈", "C": "🥉", "D": "🐌"}.get(
                grade, "❓"
            )

            grade_style = {
                "A+": "bold green",
                "A": "green",
                "B": "yellow",
                "C": "orange3",
                "D": "red",
            }.get(grade, "white")

            table.add_row(
                result["name"],
                mean_time,
                f"[{grade_style}]{grade}[/{grade_style}]",
                status,
            )

        self.console.print(table)

    def get_fastest_scenario(self) -> Optional[dict[str, Any]]:
        """Get the scenario with the fastest mean time."""
        if not self.results:
            return None

        return min(self.results, key=lambda r: r["result"]["mean"])

    def get_most_stable_scenario(self) -> Optional[dict[str, Any]]:
        """Get the scenario with the lowest standard deviation."""
        if not self.results:
            return None

        return min(self.results, key=lambda r: r["result"]["stddev"])

    def export_results(self) -> list[dict[str, Any]]:
        """Export all results for external analysis."""
        return [
            {
                "name": r["name"],
                "description": r["description"],
                "mean": r["result"]["mean"],
                "min": r["result"]["min"],
                "max": r["result"]["max"],
                "median": r["result"]["median"],
                "stddev": r["result"]["stddev"],
                "rounds": r["result"]["rounds"],
                "iterations": r["result"]["iterations"],
            }
            for r in self.results
        ]

    def clear_results(self):
        """Clear all stored results."""
        self.results.clear()


async def quick_compare(
    scenarios: list[BenchmarkScenario],
    title: str = "🚀 Quick Benchmark Comparison",
    console: Optional[Console] = None,
) -> BenchmarkComparator:
    """Run a quick comparison of multiple scenarios."""
    comparator = BenchmarkComparator(console)

    comparator.console.print(f"\n[bold blue]{title}[/bold blue]")
    comparator.console.print("=" * 50)

    for scenario in scenarios:
        await comparator.add_scenario(
            scenario.name,
            scenario.func,
            scenario.rounds,
            scenario.iterations,
            scenario.description,
        )

    comparator.display_all_results(title)
    comparator.display_performance_grades()

    return comparator


async def a_vs_b_comparison(
    name_a: str,
    func_a: Callable[[], Awaitable[Any]],
    name_b: str,
    func_b: Callable[[], Awaitable[Any]],
    rounds: int = 10,
    iterations: int = 50,
    console: Optional[Console] = None,
) -> BenchmarkComparator:
    """Quick A vs B comparison utility."""
    comparator = BenchmarkComparator(console)

    comparator.console.print(f"\n[bold magenta]⚔️  {name_a} vs {name_b}[/bold magenta]")
    comparator.console.print("=" * 50)

    await comparator.add_scenario(name_a, func_a, rounds, iterations)
    await comparator.add_scenario(name_b, func_b, rounds, iterations)

    comparator.display_pairwise_comparison(name_a, name_b)

    return comparator
