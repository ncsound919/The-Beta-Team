"""
Benchmark Runner with repeated-run support and statistical analysis.

Runs any benchmark callable N times and computes:
- Mean, median, standard deviation
- Percentiles (p50, p90, p95, p99)
- Min/max
- Regression detection vs. baseline
- Persistent history stored as JSON
"""

import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


def _mean(values: list[float]) -> float:
    """Compute arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float], mean: Optional[float] = None) -> float:
    """Compute population standard deviation."""
    if len(values) < 2:
        return 0.0
    mu = mean if mean is not None else _mean(values)
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _percentile(values: list[float], p: float) -> float:
    """Compute the p-th percentile (0–100) using linear interpolation."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    if p <= 0:
        return sorted_v[0]
    if p >= 100:
        return sorted_v[-1]
    idx = (p / 100) * (len(sorted_v) - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= len(sorted_v):
        return sorted_v[lower]
    frac = idx - lower
    return sorted_v[lower] + frac * (sorted_v[upper] - sorted_v[lower])


@dataclass
class RunStats:
    """Statistical summary of repeated benchmark runs."""
    benchmark_name: str
    iterations: int
    raw_values: list[float] = field(default_factory=list)
    mean: float = 0.0
    median: float = 0.0
    std: float = 0.0
    minimum: float = 0.0
    maximum: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_values(cls, name: str, values: list[float], metadata: dict | None = None) -> "RunStats":
        """Build a RunStats from a list of measured values."""
        if not values:
            return cls(benchmark_name=name, iterations=0, metadata=metadata or {})
        mu = _mean(values)
        return cls(
            benchmark_name=name,
            iterations=len(values),
            raw_values=list(values),
            mean=mu,
            median=_percentile(values, 50),
            std=_std(values, mu),
            minimum=min(values),
            maximum=max(values),
            p90=_percentile(values, 90),
            p95=_percentile(values, 95),
            p99=_percentile(values, 99),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "iterations": self.iterations,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "std": round(self.std, 4),
            "minimum": round(self.minimum, 4),
            "maximum": round(self.maximum, 4),
            "p90": round(self.p90, 4),
            "p95": round(self.p95, 4),
            "p99": round(self.p99, 4),
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def regression_vs(self, baseline: "RunStats", threshold_pct: float = 10.0) -> dict:
        """
        Compare this run against a baseline and flag regressions.

        A regression is flagged when the mean degrades by more than
        *threshold_pct* percent relative to the baseline mean.

        Args:
            baseline: Previous RunStats to compare against.
            threshold_pct: Percentage increase that triggers a regression flag.

        Returns:
            Dictionary with ``regressed`` flag, ``delta_pct``, and ``details``.
        """
        if baseline.mean == 0:
            return {"regressed": False, "delta_pct": 0.0, "details": "Baseline mean is 0 – cannot compare."}
        delta_pct = ((self.mean - baseline.mean) / baseline.mean) * 100
        regressed = delta_pct > threshold_pct
        return {
            "regressed": regressed,
            "delta_pct": round(delta_pct, 2),
            "baseline_mean": baseline.mean,
            "current_mean": self.mean,
            "threshold_pct": threshold_pct,
            "details": (
                f"Mean increased by {delta_pct:+.2f}% (threshold {threshold_pct}%)"
                if regressed
                else f"No regression detected ({delta_pct:+.2f}%)"
            ),
        }

    def summary_line(self) -> str:
        """Return a one-line human-readable summary."""
        return (
            f"{self.benchmark_name}: n={self.iterations} "
            f"mean={self.mean:.3f} median={self.median:.3f} "
            f"std={self.std:.3f} p95={self.p95:.3f} "
            f"min={self.minimum:.3f} max={self.maximum:.3f}"
        )


class BenchmarkRunner:
    """
    Runs a callable benchmark N times and aggregates the timing statistics.

    Supports:
    - Configurable warmup iterations (not included in statistics)
    - Configurable inter-run delay
    - Persistent JSON history for cross-session comparisons
    - Automatic regression detection vs the previous run

    Example::

        def my_benchmark() -> float:
            start = time.time()
            do_work()
            return time.time() - start

        runner = BenchmarkRunner(history_path="benchmarks.json")
        stats = runner.run("my_op", my_benchmark, iterations=20, warmup=2)
        print(stats.summary_line())
        runner.save()
    """

    def __init__(self, history_path: Optional[str] = None):
        """
        Initialise the runner.

        Args:
            history_path: Optional path to a JSON file for persisting run history.
        """
        self.history_path = history_path
        self._history: dict[str, list[dict]] = {}
        if history_path:
            self._load_history()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        name: str,
        benchmark_fn: Callable[[], float],
        iterations: int = 10,
        warmup: int = 2,
        delay_s: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> RunStats:
        """
        Execute *benchmark_fn* repeatedly and return aggregated statistics.

        The function should return the measured value (e.g. elapsed seconds).
        If it returns ``None`` the runner times the call itself.

        Args:
            name: Logical name for this benchmark.
            benchmark_fn: Callable that returns the measurement or None.
            iterations: Number of measured iterations.
            warmup: Number of warmup iterations (results discarded).
            delay_s: Sleep between iterations (seconds).
            metadata: Arbitrary key/value tags stored with the result.

        Returns:
            RunStats with full statistical summary.
        """
        # Warmup
        for _ in range(warmup):
            try:
                benchmark_fn()
            except Exception:
                pass
            if delay_s:
                time.sleep(delay_s)

        # Measured runs
        values: list[float] = []
        error_count = 0
        last_error: Optional[Exception] = None
        for _ in range(iterations):
            start = time.perf_counter()
            had_exception = False
            try:
                result = benchmark_fn()
            except Exception as exc:
                had_exception = True
                error_count += 1
                last_error = exc
                result = None
            elapsed = time.perf_counter() - start

            # Only include successful iterations in statistics.
            if not had_exception:
                values.append(result if isinstance(result, (int, float)) else elapsed)

            if delay_s:
                time.sleep(delay_s)

        # Attach error metadata (if any) without mutating caller-provided dict.
        meta = dict(metadata) if metadata is not None else {}
        if error_count:
            meta.setdefault("_error_count", error_count)
            if last_error is not None:
                meta.setdefault("_last_error", repr(last_error))

        stats = RunStats.from_values(name, values, meta)
        self._record(stats)
        return stats

    def run_suite(
        self,
        benchmarks: list[tuple[str, Callable[[], float]]],
        iterations: int = 10,
        warmup: int = 2,
    ) -> list[RunStats]:
        """
        Run a suite of named benchmarks.

        Args:
            benchmarks: List of (name, callable) pairs.
            iterations: Iterations per benchmark.
            warmup: Warmup iterations per benchmark.

        Returns:
            List of RunStats, one per benchmark.
        """
        return [self.run(name, fn, iterations=iterations, warmup=warmup) for name, fn in benchmarks]

    def get_last_run(self, name: str) -> Optional[RunStats]:
        """
        Retrieve the most recent RunStats for a benchmark name.

        Args:
            name: Benchmark name.

        Returns:
            The most recent RunStats or None if no history exists.
        """
        entries = self._history.get(name, [])
        if not entries:
            return None
        e = entries[-1]
        stats = RunStats(
            benchmark_name=e["benchmark_name"],
            iterations=e["iterations"],
            mean=e["mean"],
            median=e["median"],
            std=e["std"],
            minimum=e["minimum"],
            maximum=e["maximum"],
            p90=e["p90"],
            p95=e["p95"],
            p99=e["p99"],
            timestamp=e["timestamp"],
            metadata=e.get("metadata", {}),
        )
        return stats

    def check_regression(
        self,
        current: RunStats,
        threshold_pct: float = 10.0,
    ) -> dict:
        """
        Compare *current* stats against the previous run for the same benchmark.

        Args:
            current: Freshly collected RunStats.
            threshold_pct: Percentage increase that triggers a regression flag.

        Returns:
            Regression report dictionary.
        """
        entries = self._history.get(current.benchmark_name, [])
        # The last entry is the one we just appended; the second-to-last is previous.
        if len(entries) < 2:
            return {"regressed": False, "delta_pct": 0.0, "details": "No previous run to compare against."}
        prev = entries[-2]
        baseline = RunStats(
            benchmark_name=prev["benchmark_name"],
            iterations=prev["iterations"],
            mean=prev["mean"],
            median=prev["median"],
            std=prev["std"],
            minimum=prev["minimum"],
            maximum=prev["maximum"],
            p90=prev["p90"],
            p95=prev["p95"],
            p99=prev["p99"],
            timestamp=prev["timestamp"],
        )
        return current.regression_vs(baseline, threshold_pct)

    def history(self, name: str) -> list[dict]:
        """
        Return full run history for a benchmark.

        Args:
            name: Benchmark name.

        Returns:
            List of run dictionaries in chronological order.
        """
        return list(self._history.get(name, []))

    def save(self) -> None:
        """Persist history to JSON (no-op if no history_path set)."""
        if not self.history_path:
            return
        path = Path(self.history_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(self, stats: RunStats) -> None:
        """Append stats to in-memory history."""
        if stats.benchmark_name not in self._history:
            self._history[stats.benchmark_name] = []
        self._history[stats.benchmark_name].append(stats.to_dict())

    def _load_history(self) -> None:
        """Load history from JSON file if it exists."""
        path = Path(self.history_path)
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._history = data
            except (json.JSONDecodeError, OSError):
                self._history = {}
