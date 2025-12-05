"""Unit tests for Beta Team SDK core components."""

import tempfile
from datetime import datetime

import pytest

from beta_team.sdk.core.base import (
    BaseAdapter,
    BenchmarkMetrics,
    SoftwareType,
    TestResult,
    TestStatus,
)
from beta_team.sdk.core.registry import AdapterRegistry


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_create_passed_result(self):
        """Test creating a passed test result."""
        result = TestResult(
            name="test_login",
            status=TestStatus.PASSED,
            duration=1.5,
        )
        assert result.name == "test_login"
        assert result.status == TestStatus.PASSED
        assert result.duration == 1.5
        assert result.error_message is None

    def test_create_failed_result_with_error(self):
        """Test creating a failed test result with error message."""
        result = TestResult(
            name="test_submit",
            status=TestStatus.FAILED,
            duration=2.3,
            error_message="Button not found",
        )
        assert result.status == TestStatus.FAILED
        assert result.error_message == "Button not found"

    def test_to_dict(self):
        """Test converting test result to dictionary."""
        result = TestResult(
            name="test_checkout",
            status=TestStatus.PASSED,
            duration=0.5,
            metadata={"browser": "chrome"},
        )
        data = result.to_dict()
        assert data["name"] == "test_checkout"
        assert data["status"] == "passed"
        assert data["duration"] == 0.5
        assert data["metadata"]["browser"] == "chrome"
        assert "timestamp" in data


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics dataclass."""

    def test_default_values(self):
        """Test default metric values."""
        metrics = BenchmarkMetrics()
        assert metrics.load_time == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.crash_count == 0
        assert metrics.ui_stability_score == 100.0

    def test_custom_values(self):
        """Test setting custom metric values."""
        metrics = BenchmarkMetrics(
            load_time=2.5,
            memory_usage_mb=512,
            cpu_usage_percent=45.3,
            crash_count=1,
        )
        assert metrics.load_time == 2.5
        assert metrics.memory_usage_mb == 512
        assert metrics.cpu_usage_percent == 45.3
        assert metrics.crash_count == 1

    def test_custom_metrics(self):
        """Test adding custom metrics."""
        metrics = BenchmarkMetrics()
        metrics.custom_metrics["fps"] = 60
        metrics.custom_metrics["latency_ms"] = 15
        assert metrics.custom_metrics["fps"] == 60
        assert metrics.custom_metrics["latency_ms"] == 15

    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = BenchmarkMetrics(load_time=1.0, memory_usage_mb=256)
        data = metrics.to_dict()
        assert data["load_time"] == 1.0
        assert data["memory_usage_mb"] == 256
        assert "custom_metrics" in data


class TestAdapterRegistry:
    """Tests for AdapterRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        AdapterRegistry.clear()

    def test_register_adapter(self):
        """Test registering an adapter class."""
        from beta_team.sdk.adapters.web_adapter import WebAdapter
        
        AdapterRegistry.register(WebAdapter, "web")
        assert "web" in AdapterRegistry.list_adapters()

    def test_get_adapter_class(self):
        """Test retrieving a registered adapter class."""
        from beta_team.sdk.adapters.game_adapter import GameAdapter
        
        AdapterRegistry.register(GameAdapter, "game")
        adapter_class = AdapterRegistry.get_adapter_class("game")
        assert adapter_class == GameAdapter

    def test_create_adapter(self):
        """Test creating an adapter instance."""
        from beta_team.sdk.adapters.windows_adapter import WindowsAdapter
        
        AdapterRegistry.register(WindowsAdapter, "windows")
        adapter = AdapterRegistry.create_adapter("windows")
        assert adapter is not None
        assert isinstance(adapter, WindowsAdapter)

    def test_get_nonexistent_adapter(self):
        """Test getting an adapter that doesn't exist."""
        result = AdapterRegistry.get_adapter_class("nonexistent")
        assert result is None

    def test_list_adapters(self):
        """Test listing all registered adapters."""
        from beta_team.sdk.adapters.web_adapter import WebAdapter
        from beta_team.sdk.adapters.game_adapter import GameAdapter
        
        AdapterRegistry.register(WebAdapter, "web")
        AdapterRegistry.register(GameAdapter, "game")
        adapters = AdapterRegistry.list_adapters()
        assert "web" in adapters
        assert "game" in adapters


class TestSoftwareType:
    """Tests for SoftwareType enum."""

    def test_software_types_exist(self):
        """Test that all software types are defined."""
        assert SoftwareType.VIDEO_GAME.value == "video_game"
        assert SoftwareType.VST_PLUGIN.value == "vst_plugin"
        assert SoftwareType.DAW.value == "daw"
        assert SoftwareType.WEB_APP.value == "web_app"
        assert SoftwareType.WINDOWS_APP.value == "windows_app"
        assert SoftwareType.FINTECH.value == "fintech"
        assert SoftwareType.BIOTECH.value == "biotech"


class TestTestStatus:
    """Tests for TestStatus enum."""

    def test_status_values(self):
        """Test that all test statuses are defined."""
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"
