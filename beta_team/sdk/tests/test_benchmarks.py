"""
Tests for BenchmarkRunner and RunStats.

Covers:
- Statistical computations (mean, median, std, percentiles)
- Repeated run aggregation
- Regression detection
- History persistence
- Suite execution
"""

import json
import math
import os
import tempfile
import time

import pytest

from beta_team.sdk.benchmarks.runner import (
    BenchmarkRunner,
    RunStats,
    _mean,
    _std,
    _percentile,
)
from beta_team.sdk.analytics.trend import (
    _linear_trend,
    _moving_average,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _constant_fn(value: float):
    """Return a benchmark callable that always returns the given value."""
    def fn():
        return value
    return fn


def _increasing_fn(start: float = 0.1, step: float = 0.01):
    """Return a callable whose return value increases each call."""
    state = {"v": start}
    def fn():
        v = state["v"]
        state["v"] += step
        return v
    return fn


# ---------------------------------------------------------------------------
# Internal math helpers
# ---------------------------------------------------------------------------

class TestMathHelpers:
    """Unit tests for the internal pure-Python statistics helpers."""

    def test_mean_basic(self):
        assert _mean([1, 2, 3, 4, 5]) == pytest.approx(3.0)

    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_mean_single(self):
        assert _mean([42.0]) == pytest.approx(42.0)

    @pytest.mark.parametrize("values,expected", [
        ([2, 2, 2, 2], 0.0),
        ([0, 10], pytest.approx(5.0)),
    ])
    def test_std_basic(self, values, expected):
        assert _std(values) == expected

    def test_std_empty(self):
        assert _std([]) == 0.0

    def test_std_single(self):
        assert _std([7.0]) == 0.0

    def test_percentile_median(self):
        result = _percentile([1, 2, 3, 4, 5], 50)
        assert result == pytest.approx(3.0)

    def test_percentile_min(self):
        assert _percentile([1, 2, 3], 0) == 1

    def test_percentile_max(self):
        assert _percentile([1, 2, 3], 100) == 3

    def test_percentile_empty(self):
        assert _percentile([], 50) == 0.0

    def test_percentile_p95(self):
        values = list(range(1, 101))  # 1..100
        # p95 via linear interpolation: idx = 0.95*99=94.05 → 95 + 0.05*(96-95) = 95.05
        assert _percentile(values, 95) == pytest.approx(95.05, abs=0.01)

    def test_linear_trend_constant(self):
        assert _linear_trend([5, 5, 5, 5]) == pytest.approx(0.0, abs=1e-9)

    def test_linear_trend_increasing(self):
        assert _linear_trend([1, 2, 3, 4, 5]) > 0

    def test_linear_trend_decreasing(self):
        assert _linear_trend([5, 4, 3, 2, 1]) < 0

    def test_linear_trend_single(self):
        assert _linear_trend([42.0]) == 0.0

    def test_moving_average_window1(self):
        v = [1.0, 2.0, 3.0]
        assert _moving_average(v, 1) == pytest.approx(v)

    def test_moving_average_full(self):
        result = _moving_average([2.0, 4.0, 6.0], window=3)
        assert result[-1] == pytest.approx(4.0)

    def test_moving_average_empty(self):
        assert _moving_average([], 3) == []


# ---------------------------------------------------------------------------
# RunStats
# ---------------------------------------------------------------------------

class TestRunStats:
    """Tests for RunStats dataclass and factory."""

    def test_from_values_basic(self):
        stats = RunStats.from_values("op", [1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats.iterations == 5
        assert stats.mean == pytest.approx(3.0)
        assert stats.minimum == pytest.approx(1.0)
        assert stats.maximum == pytest.approx(5.0)

    def test_from_values_empty(self):
        stats = RunStats.from_values("op", [])
        assert stats.iterations == 0
        assert stats.mean == 0.0

    def test_from_values_single(self):
        stats = RunStats.from_values("op", [7.0])
        assert stats.mean == pytest.approx(7.0)
        assert stats.std == 0.0

    def test_percentiles_computed(self):
        values = [float(i) for i in range(1, 101)]
        stats = RunStats.from_values("op", values)
        assert stats.p90 > stats.median
        assert stats.p95 > stats.p90
        assert stats.p99 > stats.p95

    def test_to_dict_keys(self):
        stats = RunStats.from_values("op", [1.0, 2.0, 3.0])
        d = stats.to_dict()
        for key in ("benchmark_name", "iterations", "mean", "median", "std",
                    "minimum", "maximum", "p90", "p95", "p99", "timestamp", "metadata"):
            assert key in d

    def test_regression_vs_no_regression(self):
        baseline = RunStats.from_values("op", [1.0, 1.0, 1.0])
        current = RunStats.from_values("op", [1.05, 1.05, 1.05])  # +5 % – under 10 % threshold
        report = current.regression_vs(baseline, threshold_pct=10.0)
        assert not report["regressed"]

    def test_regression_vs_regression_detected(self):
        baseline = RunStats.from_values("op", [1.0, 1.0, 1.0])
        current = RunStats.from_values("op", [1.5, 1.5, 1.5])  # +50 %
        report = current.regression_vs(baseline, threshold_pct=10.0)
        assert report["regressed"]
        assert report["delta_pct"] == pytest.approx(50.0, abs=0.1)

    def test_regression_vs_zero_baseline(self):
        baseline = RunStats.from_values("op", [0.0])
        current = RunStats.from_values("op", [1.0])
        report = current.regression_vs(baseline)
        assert not report["regressed"]  # Cannot compare – no regression flagged

    def test_summary_line(self):
        stats = RunStats.from_values("my_op", [0.1, 0.2, 0.3])
        line = stats.summary_line()
        assert "my_op" in line
        assert "mean=" in line
        assert "p95=" in line

    def test_metadata_stored(self):
        stats = RunStats.from_values("op", [1.0], metadata={"env": "ci"})
        assert stats.metadata["env"] == "ci"
        assert stats.to_dict()["metadata"]["env"] == "ci"


# ---------------------------------------------------------------------------
# BenchmarkRunner
# ---------------------------------------------------------------------------

class TestBenchmarkRunner:
    """Tests for BenchmarkRunner orchestration."""

    @pytest.mark.benchmark
    def test_run_returns_run_stats(self):
        runner = BenchmarkRunner()
        stats = runner.run("const", _constant_fn(0.5), iterations=5, warmup=0)
        assert isinstance(stats, RunStats)
        assert stats.iterations == 5

    @pytest.mark.benchmark
    def test_run_correct_mean(self):
        runner = BenchmarkRunner()
        stats = runner.run("const", _constant_fn(2.0), iterations=10, warmup=0)
        assert stats.mean == pytest.approx(2.0, abs=1e-6)

    @pytest.mark.benchmark
    def test_warmup_not_counted(self):
        runner = BenchmarkRunner()
        stats = runner.run("const", _constant_fn(1.0), iterations=5, warmup=3)
        assert stats.iterations == 5

    @pytest.mark.benchmark
    def test_fn_returning_none_times_itself(self):
        """If the benchmark returns None, elapsed wall-time is used."""
        def slow_fn():
            time.sleep(0.01)
            # returns None implicitly

        runner = BenchmarkRunner()
        stats = runner.run("timed", slow_fn, iterations=3, warmup=0)
        assert stats.mean >= 0.01

    @pytest.mark.benchmark
    def test_exception_in_fn_excludes_errored_iterations(self):
        """Errored iterations are excluded from stats; error count is stored in metadata."""
        call_count = {"n": 0}
        def fragile():
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                raise RuntimeError("Simulated failure")
            return 0.1

        runner = BenchmarkRunner()
        stats = runner.run("fragile", fragile, iterations=4, warmup=0)
        # 4 calls; calls 2 and 4 raise → 2 successes recorded
        assert stats.iterations == 2
        assert stats.mean == pytest.approx(0.1, abs=1e-6)
        assert stats.metadata.get("_error_count") == 2
        assert "_last_error" in stats.metadata

    @pytest.mark.benchmark
    def test_run_suite(self):
        runner = BenchmarkRunner()
        suite = [("a", _constant_fn(1.0)), ("b", _constant_fn(2.0))]
        results = runner.run_suite(suite, iterations=5, warmup=0)
        assert len(results) == 2
        assert results[0].benchmark_name == "a"
        assert results[1].benchmark_name == "b"

    @pytest.mark.benchmark
    def test_history_accumulates(self):
        runner = BenchmarkRunner()
        runner.run("op", _constant_fn(1.0), iterations=3, warmup=0)
        runner.run("op", _constant_fn(2.0), iterations=3, warmup=0)
        assert len(runner.history("op")) == 2

    @pytest.mark.benchmark
    def test_get_last_run(self):
        runner = BenchmarkRunner()
        runner.run("op", _constant_fn(1.0), iterations=3, warmup=0)
        runner.run("op", _constant_fn(5.0), iterations=3, warmup=0)
        last = runner.get_last_run("op")
        assert last is not None
        assert last.mean == pytest.approx(5.0, abs=1e-6)

    @pytest.mark.benchmark
    def test_get_last_run_none_if_missing(self):
        runner = BenchmarkRunner()
        assert runner.get_last_run("nonexistent") is None

    @pytest.mark.benchmark
    def test_check_regression_detects_regression(self):
        runner = BenchmarkRunner()
        runner.run("op", _constant_fn(1.0), iterations=5, warmup=0)
        current = runner.run("op", _constant_fn(2.0), iterations=5, warmup=0)
        report = runner.check_regression(current, threshold_pct=10.0)
        assert report["regressed"]

    @pytest.mark.benchmark
    def test_check_regression_no_regression(self):
        runner = BenchmarkRunner()
        runner.run("op", _constant_fn(1.0), iterations=5, warmup=0)
        current = runner.run("op", _constant_fn(1.05), iterations=5, warmup=0)
        report = runner.check_regression(current, threshold_pct=10.0)
        assert not report["regressed"]

    @pytest.mark.benchmark
    def test_check_regression_first_run(self):
        runner = BenchmarkRunner()
        current = runner.run("op", _constant_fn(1.0), iterations=5, warmup=0)
        report = runner.check_regression(current)
        assert not report["regressed"]
        assert "No previous run" in report["details"]


class TestBenchmarkRunnerPersistence:
    """Tests for BenchmarkRunner JSON history persistence."""

    @pytest.mark.benchmark
    def test_save_and_reload(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            runner = BenchmarkRunner(history_path=path)
            runner.run("op", _constant_fn(3.0), iterations=4, warmup=0)
            runner.save()

            runner2 = BenchmarkRunner(history_path=path)
            assert "op" in runner2._history
            assert len(runner2._history["op"]) == 1
            assert runner2._history["op"][0]["mean"] == pytest.approx(3.0, abs=1e-6)
        finally:
            os.unlink(path)

    @pytest.mark.benchmark
    def test_corrupted_history_handled(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("NOT VALID JSON {{{")
            path = f.name
        try:
            # Should not raise
            runner = BenchmarkRunner(history_path=path)
            assert runner._history == {}
        finally:
            os.unlink(path)

    @pytest.mark.benchmark
    def test_history_path_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nested", "dir", "history.json")
            runner = BenchmarkRunner(history_path=path)
            runner.run("op", _constant_fn(1.0), iterations=2, warmup=0)
            runner.save()
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "op" in data

    @pytest.mark.benchmark
    def test_save_noop_without_path(self):
        runner = BenchmarkRunner()  # no history_path
        runner.run("op", _constant_fn(1.0), iterations=2, warmup=0)
        runner.save()  # Should not raise


# ---------------------------------------------------------------------------
# Parametrized cross-benchmark validation
# ---------------------------------------------------------------------------

@pytest.mark.benchmark
@pytest.mark.parametrize("iterations", [1, 5, 20])
def test_iteration_counts(iterations):
    runner = BenchmarkRunner()
    stats = runner.run("param_test", _constant_fn(0.1), iterations=iterations, warmup=0)
    assert stats.iterations == iterations


@pytest.mark.benchmark
@pytest.mark.parametrize("value,threshold,expect_regression", [
    (1.0, 10.0, False),
    (1.05, 10.0, False),  # +5% – below threshold
    (1.15, 10.0, True),   # +15% > 10%
    (2.0, 10.0, True),    # +100%
    (0.5, 10.0, False),   # improvement (decrease)
])
def test_regression_thresholds(value, threshold, expect_regression):
    runner = BenchmarkRunner()
    runner.run("op", _constant_fn(1.0), iterations=5, warmup=0)
    current = runner.run("op", _constant_fn(value), iterations=5, warmup=0)
    report = runner.check_regression(current, threshold_pct=threshold)
    assert report["regressed"] == expect_regression
