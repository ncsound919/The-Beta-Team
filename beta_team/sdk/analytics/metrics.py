"""
Metrics Collection for Beta Testing.

Provides real-time metrics collection similar to Statsig for tracking:
- Crash rates
- Engagement metrics
- Test pass/fail rates
- Performance trends
- Flaky test detection
"""

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class TestMetric:
    """A single test metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class RealTimeMetrics:
    """Container for real-time metrics data."""
    crash_rate: float = 0.0
    pass_rate: float = 0.0
    flaky_test_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    avg_load_time_ms: float = 0.0
    active_tests: int = 0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    engagement_score: float = 0.0
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "crash_rate": self.crash_rate,
            "pass_rate": self.pass_rate,
            "flaky_test_rate": self.flaky_test_rate,
            "avg_response_time_ms": self.avg_response_time_ms,
            "avg_load_time_ms": self.avg_load_time_ms,
            "active_tests": self.active_tests,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "engagement_score": self.engagement_score,
            "custom_metrics": self.custom_metrics,
        }


class MetricsCollector:
    """
    Collector for test metrics with real-time aggregation.

    Similar to Statsig, provides:
    - Real-time crash rate tracking
    - Engagement metrics
    - Flaky test detection
    - Historical trend analysis
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the metrics collector.

        Args:
            storage_path: Path to store metrics history. If None, metrics are in-memory only.
        """
        self.storage_path = storage_path
        self._metrics: list[TestMetric] = []
        self._test_results: dict[str, list[bool]] = defaultdict(list)
        self._crash_events: list[datetime] = []
        self._response_times: list[float] = []
        self._load_times: list[float] = []
        self._session_start = datetime.now()

        if storage_path:
            self._load_history()

    def record_metric(self, name: str, value: float, tags: Optional[dict] = None, metadata: Optional[dict] = None) -> None:
        """
        Record a single metric data point.

        Args:
            name: Metric name.
            value: Metric value.
            tags: Optional tags for filtering.
            metadata: Optional additional data.
        """
        metric = TestMetric(
            name=name,
            value=value,
            tags=tags or {},
            metadata=metadata or {},
        )
        self._metrics.append(metric)

    def record_test_result(self, test_name: str, passed: bool) -> None:
        """
        Record a test result for flaky detection.

        Args:
            test_name: Name of the test.
            passed: Whether the test passed.
        """
        self._test_results[test_name].append(passed)

    def record_crash(self) -> None:
        """Record a crash event."""
        self._crash_events.append(datetime.now())

    def record_response_time(self, time_ms: float) -> None:
        """Record a response time measurement."""
        self._response_times.append(time_ms)

    def record_load_time(self, time_ms: float) -> None:
        """Record a load time measurement."""
        self._load_times.append(time_ms)

    def get_real_time_metrics(self) -> RealTimeMetrics:
        """
        Calculate current real-time metrics.

        Returns:
            RealTimeMetrics with current values.
        """
        metrics = RealTimeMetrics()

        # Calculate pass rate
        total = sum(len(results) for results in self._test_results.values())
        passed = sum(sum(results) for results in self._test_results.values())
        if total > 0:
            metrics.pass_rate = passed / total * 100
            metrics.total_tests = total
            metrics.passed_tests = passed
            metrics.failed_tests = total - passed

        # Calculate crash rate
        session_hours = (datetime.now() - self._session_start).total_seconds() / 3600
        if session_hours > 0:
            metrics.crash_rate = len(self._crash_events) / session_hours

        # Calculate flaky test rate
        flaky_count = 0
        for test_name, results in self._test_results.items():
            if len(results) >= 2:
                # A test is flaky if it has mixed pass/fail results
                if 0 < sum(results) < len(results):
                    flaky_count += 1

        if len(self._test_results) > 0:
            metrics.flaky_test_rate = flaky_count / len(self._test_results) * 100

        # Calculate average times
        if self._response_times:
            metrics.avg_response_time_ms = sum(self._response_times) / len(self._response_times)
        if self._load_times:
            metrics.avg_load_time_ms = sum(self._load_times) / len(self._load_times)

        # Calculate engagement (simplified)
        metrics.engagement_score = min(100, metrics.pass_rate * 0.8 + (100 - metrics.flaky_test_rate) * 0.2)

        return metrics

    def get_flaky_tests(self, min_runs: int = 3) -> list[dict]:
        """
        Get list of flaky tests.

        Args:
            min_runs: Minimum number of runs to consider.

        Returns:
            List of flaky test info.
        """
        flaky = []
        for test_name, results in self._test_results.items():
            if len(results) >= min_runs:
                pass_count = sum(results)
                fail_count = len(results) - pass_count
                if pass_count > 0 and fail_count > 0:
                    flaky.append({
                        "name": test_name,
                        "total_runs": len(results),
                        "pass_count": pass_count,
                        "fail_count": fail_count,
                        "flakiness_rate": min(pass_count, fail_count) / len(results) * 100,
                    })

        return sorted(flaky, key=lambda x: x["flakiness_rate"], reverse=True)

    def get_trend_data(self, metric_name: str, last_n: int = 100) -> list[dict]:
        """
        Get historical trend data for a metric.

        Args:
            metric_name: Name of the metric.
            last_n: Number of recent data points.

        Returns:
            List of metric data points.
        """
        filtered = [m for m in self._metrics if m.name == metric_name]
        return [m.to_dict() for m in filtered[-last_n:]]

    def save(self) -> None:
        """Save metrics to storage."""
        if not self.storage_path:
            return

        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        data = {
            "session_start": self._session_start.isoformat(),
            "metrics": [m.to_dict() for m in self._metrics],
            "test_results": dict(self._test_results),
            "crash_events": [e.isoformat() for e in self._crash_events],
            "response_times": self._response_times,
            "load_times": self._load_times,
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_history(self) -> None:
        """Load historical metrics from storage."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            for m in data.get("metrics", []):
                self._metrics.append(TestMetric(
                    name=m["name"],
                    value=m["value"],
                    timestamp=datetime.fromisoformat(m["timestamp"]),
                    tags=m.get("tags", {}),
                    metadata=m.get("metadata", {}),
                ))

            for test_name, results in data.get("test_results", {}).items():
                self._test_results[test_name] = results

            for e in data.get("crash_events", []):
                self._crash_events.append(datetime.fromisoformat(e))

            self._response_times = data.get("response_times", [])
            self._load_times = data.get("load_times", [])

        except (json.JSONDecodeError, KeyError):
            pass

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._test_results.clear()
        self._crash_events.clear()
        self._response_times.clear()
        self._load_times.clear()
        self._session_start = datetime.now()

    def export_metrics(self) -> dict:
        """
        Export all metrics as a dictionary.

        Returns:
            Dictionary with all collected metrics.
        """
        return {
            "real_time": self.get_real_time_metrics().to_dict(),
            "flaky_tests": self.get_flaky_tests(),
            "all_metrics": [m.to_dict() for m in self._metrics],
            "test_results": dict(self._test_results),
            "crash_count": len(self._crash_events),
        }
