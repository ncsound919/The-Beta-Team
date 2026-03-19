"""
Tests for TrendAnalyzer, RunSnapshot, and TrendReport.

Covers:
- Snapshot ingestion and retrieval
- Per-metric trend direction detection (improving / degrading / stable)
- Regression flagging with configurable thresholds
- Full report generation
- Bullet-summary output
- Edge cases (empty data, single snapshot, zero values)
"""

import pytest

from beta_team.sdk.analytics.trend import (
    RunSnapshot,
    TrendAnalyzer,
    TrendReport,
    _linear_trend,
    _moving_average,
    _mean,
    _std,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshots(pass_rates: list[float], response_times: list[float] | None = None) -> list[RunSnapshot]:
    """Build a list of RunSnapshots from pass-rate and optional response-time series."""
    rts = response_times or [100.0] * len(pass_rates)
    return [
        RunSnapshot(
            run_id=f"run-{i+1}",
            pass_rate=pass_rates[i],
            avg_response_time_ms=rts[i],
        )
        for i in range(len(pass_rates))
    ]


# ---------------------------------------------------------------------------
# RunSnapshot
# ---------------------------------------------------------------------------

class TestRunSnapshot:
    """Tests for the RunSnapshot dataclass."""

    def test_defaults(self):
        snap = RunSnapshot(run_id="r1")
        assert snap.pass_rate == 0.0
        assert snap.avg_response_time_ms == 0.0
        assert snap.crash_rate == 0.0

    def test_to_dict_keys(self):
        snap = RunSnapshot(run_id="r1", pass_rate=90.0, avg_response_time_ms=150.0)
        d = snap.to_dict()
        for key in ("run_id", "timestamp", "pass_rate", "avg_response_time_ms",
                    "avg_load_time_ms", "crash_rate", "flaky_rate", "extra"):
            assert key in d

    def test_to_dict_values(self):
        snap = RunSnapshot(run_id="r1", pass_rate=85.0, crash_rate=0.5)
        d = snap.to_dict()
        assert d["pass_rate"] == 85.0
        assert d["crash_rate"] == 0.5


# ---------------------------------------------------------------------------
# TrendAnalyzer – basic usage
# ---------------------------------------------------------------------------

class TestTrendAnalyzerBasic:
    """Core TrendAnalyzer functionality."""

    def test_add_snapshot(self):
        az = TrendAnalyzer()
        az.add_snapshot(RunSnapshot(run_id="r1", pass_rate=90.0))
        assert len(az.snapshots()) == 1

    def test_add_from_dict(self):
        az = TrendAnalyzer()
        az.add_from_dict({"run_id": "r1", "pass_rate": 80.0})
        assert az.snapshots()[0].pass_rate == 80.0

    def test_clear(self):
        az = TrendAnalyzer()
        az.add_snapshot(RunSnapshot(run_id="r1"))
        az.clear()
        assert len(az.snapshots()) == 0

    def test_analyze_empty(self):
        az = TrendAnalyzer()
        report = az.analyze("pass_rate")
        assert report.direction == "stable"
        assert report.mean == 0.0
        assert not report.regressed

    def test_analyze_single_snapshot(self):
        az = TrendAnalyzer()
        az.add_snapshot(RunSnapshot(run_id="r1", pass_rate=90.0))
        report = az.analyze("pass_rate")
        assert report.mean == pytest.approx(90.0)
        assert not report.regressed


# ---------------------------------------------------------------------------
# TrendAnalyzer – direction detection
# ---------------------------------------------------------------------------

@pytest.mark.analytics
class TestTrendDirection:
    """Tests for trend direction (improving / degrading / stable)."""

    def test_pass_rate_improving(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([70, 80, 90, 95]):
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert report.direction == "improving"

    def test_pass_rate_degrading(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([95, 90, 80, 70]):
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert report.direction == "degrading"

    def test_pass_rate_stable(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90, 90, 90, 90]):
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert report.direction == "stable"

    def test_response_time_improving(self):
        """Decreasing response time is an improvement."""
        az = TrendAnalyzer()
        for snap in _make_snapshots([90]*4, response_times=[250, 200, 150, 100]):
            az.add_snapshot(snap)
        report = az.analyze("avg_response_time_ms")
        assert report.direction == "improving"

    def test_response_time_degrading(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90]*4, response_times=[100, 150, 200, 300]):
            az.add_snapshot(snap)
        report = az.analyze("avg_response_time_ms")
        assert report.direction == "degrading"


# ---------------------------------------------------------------------------
# TrendAnalyzer – regression detection
# ---------------------------------------------------------------------------

@pytest.mark.analytics
class TestRegressionDetection:
    """Tests for regression flagging."""

    def test_pass_rate_regression_detected(self):
        az = TrendAnalyzer(regression_threshold_pct=10.0)
        for snap in _make_snapshots([90, 90, 90, 70]):  # drops 22 %
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert report.regressed

    def test_pass_rate_no_regression_small_drop(self):
        az = TrendAnalyzer(regression_threshold_pct=10.0)
        for snap in _make_snapshots([90, 90, 90, 85]):  # drops ~5 %
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert not report.regressed

    def test_response_time_regression_detected(self):
        az = TrendAnalyzer(regression_threshold_pct=10.0)
        for snap in _make_snapshots([90]*4, response_times=[100, 100, 100, 150]):  # +50 %
            az.add_snapshot(snap)
        report = az.analyze("avg_response_time_ms")
        assert report.regressed

    def test_response_time_no_regression_small_increase(self):
        az = TrendAnalyzer(regression_threshold_pct=20.0)
        for snap in _make_snapshots([90]*4, response_times=[100, 105, 108, 112]):  # +12 %
            az.add_snapshot(snap)
        report = az.analyze("avg_response_time_ms")
        assert not report.regressed

    def test_custom_threshold(self):
        az = TrendAnalyzer(regression_threshold_pct=50.0)
        for snap in _make_snapshots([90, 90, 90, 60]):  # drops 33 % – under 50 % threshold
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert not report.regressed

    @pytest.mark.parametrize("pass_rates,threshold,expect", [
        ([100, 100, 100, 60], 10.0, True),   # -40 %  regression (pass_rate drop)
        ([100, 100, 100, 95], 10.0, False),  # -5 %   no regression
        ([80, 80, 80, 160], 10.0, False),    # +100 % pass_rate improvement – NOT a regression
    ])
    def test_parametrized_regression(self, pass_rates, threshold, expect):
        az = TrendAnalyzer(regression_threshold_pct=threshold)
        for snap in _make_snapshots(pass_rates):
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        assert report.regressed == expect


# ---------------------------------------------------------------------------
# TrendAnalyzer – full_report and bullet_summary
# ---------------------------------------------------------------------------

@pytest.mark.analytics
class TestFullReport:
    """Tests for full_report() and bullet_summary()."""

    def test_full_report_structure(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90, 85, 80]):
            az.add_snapshot(snap)
        report = az.full_report()
        assert "generated_at" in report
        assert "snapshot_count" in report
        assert "trends" in report
        assert "snapshots" in report

    def test_full_report_snapshot_count(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90, 80, 70]):
            az.add_snapshot(snap)
        assert az.full_report()["snapshot_count"] == 3

    def test_bullet_summary_returns_list(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90, 85, 80]):
            az.add_snapshot(snap)
        bullets = az.bullet_summary()
        assert isinstance(bullets, list)
        assert len(bullets) > 0

    def test_bullet_summary_contains_emoji(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([90, 85, 70]):  # degrading pass rate
            az.add_snapshot(snap)
        bullets = az.bullet_summary()
        text = "\n".join(bullets)
        # Should contain at least one status emoji
        assert any(icon in text for icon in ("🔴", "🟢", "🟡"))

    def test_regression_bullet_flagged_red(self):
        az = TrendAnalyzer(regression_threshold_pct=5.0)
        for snap in _make_snapshots([90, 90, 90, 50]):  # severe drop
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        bullet = report.bullet()
        assert "🔴" in bullet

    def test_improving_bullet_flagged_green(self):
        az = TrendAnalyzer()
        for snap in _make_snapshots([70, 80, 90, 95]):  # improving
            az.add_snapshot(snap)
        report = az.analyze("pass_rate")
        bullet = report.bullet()
        assert "🟢" in bullet


# ---------------------------------------------------------------------------
# TrendReport
# ---------------------------------------------------------------------------

class TestTrendReport:
    """Unit tests for TrendReport."""

    def _make_report(self, regressed=False, direction="stable", change_pct=0.0):
        return TrendReport(
            metric="pass_rate",
            direction=direction,
            slope=0.0,
            mean=85.0,
            std=2.0,
            first_value=85.0,
            last_value=85.0,
            change_pct=change_pct,
            regressed=regressed,
            threshold_pct=10.0,
            details="Test details",
        )

    def test_to_dict_keys(self):
        report = self._make_report()
        d = report.to_dict()
        for key in ("metric", "direction", "slope", "mean", "std", "first_value",
                    "last_value", "change_pct", "regressed", "threshold_pct", "details"):
            assert key in d

    def test_bullet_regressed(self):
        report = self._make_report(regressed=True, direction="degrading")
        assert "🔴" in report.bullet()

    def test_bullet_improving(self):
        report = self._make_report(direction="improving")
        assert "🟢" in report.bullet()

    def test_bullet_stable(self):
        report = self._make_report(direction="stable")
        assert "🟡" in report.bullet()
