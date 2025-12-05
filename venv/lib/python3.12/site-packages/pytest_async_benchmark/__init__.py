"""pytest-async-benchmark: Modern pytest benchmarking for async code. 🚀"""

__version__ = "0.2.0"
__author__ = "Mihai Farcas"
__email__ = "contact@mihai.ltd"

from .analytics import benchmark_summary, compare_benchmarks, performance_grade
from .comparison import (
    BenchmarkComparator,
    BenchmarkScenario,
    a_vs_b_comparison,
    quick_compare,
)
from .display import display_comparison_table, format_speedup, format_time
from .plugin import async_benchmark
from .runner import AsyncBenchmarkRunner

__all__ = [
    "async_benchmark",
    "AsyncBenchmarkRunner",
    "BenchmarkComparator",
    "BenchmarkScenario",
    "quick_compare",
    "a_vs_b_comparison",
    "display_comparison_table",
    "format_time",
    "format_speedup",
    "compare_benchmarks",
    "performance_grade",
    "benchmark_summary",
]
