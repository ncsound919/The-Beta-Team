"""
Trend Analysis for Beta Testing.

Provides cross-run trend analysis and performance regression detection
by comparing successive metric snapshots over time.

Key features:
- Cross-run pass-rate trend detection (improving / degrading / stable)
- Response-time regression alerts with configurable thresholds
- Moving-average smoothing for noisy data
- Exportable trend report (JSON + plain-text bullets)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Internal maths helpers (stdlib only)
# ---------------------------------------------------------------------------

def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))


def _linear_trend(values: list[float]) -> float:
    """Return the slope of a simple linear regression (y ~ a + b*x).

    A positive slope means values are growing over time.
    """
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = _mean(xs)
    my = _mean(values)
    num = sum((xs[i] - mx) * (values[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    return num / den if den else 0.0


def _moving_average(values: list[float], window: int = 3) -> list[float]:
    """Compute a trailing moving average with the given window size."""
    if window <= 0 or not values:
        return list(values)
    result: list[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        result.append(_mean(values[start : i + 1]))
    return result


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RunSnapshot:
    """A single test-run snapshot for trend tracking."""
    run_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    pass_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    avg_load_time_ms: float = 0.0
    crash_rate: float = 0.0
    flaky_rate: float = 0.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "pass_rate": self.pass_rate,
            "avg_response_time_ms": self.avg_response_time_ms,
            "avg_load_time_ms": self.avg_load_time_ms,
            "crash_rate": self.crash_rate,
            "flaky_rate": self.flaky_rate,
            "extra": self.extra,
        }


@dataclass
class TrendReport:
    """Summary of trend analysis across multiple runs."""
    metric: str
    direction: str  # "improving", "degrading", "stable"
    slope: float
    mean: float
    std: float
    first_value: float
    last_value: float
    change_pct: float
    regressed: bool
    threshold_pct: float
    details: str
    smoothed_values: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "direction": self.direction,
            "slope": self.slope,
            "mean": self.mean,
            "std": self.std,
            "first_value": self.first_value,
            "last_value": self.last_value,
            "change_pct": self.change_pct,
            "regressed": self.regressed,
            "threshold_pct": self.threshold_pct,
            "details": self.details,
            "smoothed_values": self.smoothed_values,
        }

    def bullet(self) -> str:
        icon = "🔴" if self.regressed else ("🟢" if self.direction == "improving" else "🟡")
        return f"{icon} {self.metric}: {self.direction} ({self.change_pct:+.1f}%) — {self.details}"


# ---------------------------------------------------------------------------
# Main analyser
# ---------------------------------------------------------------------------

class TrendAnalyzer:
    """
    Analyses metric trends across multiple test runs.

    Usage::

        analyzer = TrendAnalyzer()
        analyzer.add_snapshot(RunSnapshot("run-1", pass_rate=90, avg_response_time_ms=200))
        analyzer.add_snapshot(RunSnapshot("run-2", pass_rate=85, avg_response_time_ms=220))
        analyzer.add_snapshot(RunSnapshot("run-3", pass_rate=80, avg_response_time_ms=250))

        report = analyzer.analyze("avg_response_time_ms", higher_is_better=False)
        print(report.bullet())

        full = analyzer.full_report()
        bullets = analyzer.bullet_summary()
    """

    # Metrics where a *lower* value is better (regression = increase)
    _LOWER_IS_BETTER = {
        "avg_response_time_ms",
        "avg_load_time_ms",
        "crash_rate",
        "flaky_rate",
    }
    # Metrics where a *higher* value is better (regression = decrease)
    _HIGHER_IS_BETTER = {"pass_rate"}

    def __init__(self, regression_threshold_pct: float = 10.0, smoothing_window: int = 3):
        """
        Initialise the analyser.

        Args:
            regression_threshold_pct: Change percentage that triggers a regression flag.
            smoothing_window: Window size for moving-average smoothing.
        """
        self.regression_threshold_pct = regression_threshold_pct
        self.smoothing_window = smoothing_window
        self._snapshots: list[RunSnapshot] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_snapshot(self, snapshot: RunSnapshot) -> None:
        """Append a run snapshot to the history."""
        self._snapshots.append(snapshot)

    def add_from_dict(self, data: dict) -> None:
        """Build and append a RunSnapshot from a dictionary."""
        self.add_snapshot(RunSnapshot(**{k: v for k, v in data.items() if k in RunSnapshot.__dataclass_fields__}))

    def analyze(self, metric: str, higher_is_better: Optional[bool] = None) -> TrendReport:
        """
        Compute the trend for a single metric.

        Args:
            metric: Name of the RunSnapshot field to analyse.
            higher_is_better: Override automatic direction inference.

        Returns:
            TrendReport for the metric.
        """
        values = self._extract(metric)

        if not values:
            return TrendReport(
                metric=metric,
                direction="stable",
                slope=0.0,
                mean=0.0,
                std=0.0,
                first_value=0.0,
                last_value=0.0,
                change_pct=0.0,
                regressed=False,
                threshold_pct=self.regression_threshold_pct,
                details="No data available.",
            )

        mu = _mean(values)
        sd = _std(values)
        slope = _linear_trend(values)
        first = values[0]
        last = values[-1]
        if first == 0 and last == 0:
            change_pct = 0.0
        else:
            denom = first if first != 0 else last
            change_pct = (last - first) / denom * 100
        smoothed = _moving_average(values, self.smoothing_window)

        # Determine if improvement or degradation
        if higher_is_better is None:
            higher_is_better = metric in self._HIGHER_IS_BETTER

        if higher_is_better:
            # Regression = decrease
            regressed = change_pct < -self.regression_threshold_pct
            if slope > 0.01:
                direction = "improving"
            elif slope < -0.01:
                direction = "degrading"
            else:
                direction = "stable"
        else:
            # Regression = increase
            regressed = change_pct > self.regression_threshold_pct
            if slope < -0.01:
                direction = "improving"
            elif slope > 0.01:
                direction = "degrading"
            else:
                direction = "stable"

        details = (
            f"Changed from {first:.2f} to {last:.2f} across {len(values)} runs "
            f"(σ={sd:.2f}). {'⚠ Regression detected.' if regressed else 'Within threshold.'}"
        )

        return TrendReport(
            metric=metric,
            direction=direction,
            slope=round(slope, 6),
            mean=round(mu, 4),
            std=round(sd, 4),
            first_value=round(first, 4),
            last_value=round(last, 4),
            change_pct=round(change_pct, 2),
            regressed=regressed,
            threshold_pct=self.regression_threshold_pct,
            details=details,
            smoothed_values=[round(v, 4) for v in smoothed],
        )

    def full_report(self) -> dict:
        """
        Analyse all standard metrics and return a combined report.

        Returns:
            Dictionary with per-metric TrendReport data and snapshot list.
        """
        all_metrics = sorted(self._LOWER_IS_BETTER | self._HIGHER_IS_BETTER)
        trends = {}
        for m in all_metrics:
            if self._extract(m):
                trends[m] = self.analyze(m).to_dict()

        return {
            "generated_at": datetime.now().isoformat(),
            "snapshot_count": len(self._snapshots),
            "trends": trends,
            "snapshots": [s.to_dict() for s in self._snapshots],
        }

    def bullet_summary(self) -> list[str]:
        """
        Return a list of human-readable bullet-point trend summaries.

        Returns:
            List of bullet strings, one per tracked metric.
        """
        all_metrics = list(self._LOWER_IS_BETTER | self._HIGHER_IS_BETTER)
        bullets = []
        for m in all_metrics:
            if self._extract(m):
                bullets.append(self.analyze(m).bullet())
        return bullets

    def snapshots(self) -> list[RunSnapshot]:
        """Return a copy of all added snapshots."""
        return list(self._snapshots)

    def clear(self) -> None:
        """Remove all snapshots."""
        self._snapshots.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract(self, metric: str) -> list[float]:
        """Extract numeric values for *metric* from all snapshots."""
        out = []
        for s in self._snapshots:
            val = getattr(s, metric, None)
            if isinstance(val, (int, float)):
                out.append(float(val))
        return out
