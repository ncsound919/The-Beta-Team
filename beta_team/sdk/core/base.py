"""
Base classes and interfaces for Beta Team SDK adapters.

This module provides the foundation for creating adapters that integrate
with various software types including video games, DAWs, web apps, and
Windows applications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TestStatus(Enum):
    """Status of a test execution."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class SoftwareType(Enum):
    """Types of software that can be tested."""
    VIDEO_GAME = "video_game"
    VST_PLUGIN = "vst_plugin"
    DAW = "daw"
    WEB_APP = "web_app"
    WINDOWS_APP = "windows_app"
    FINTECH = "fintech"
    BIOTECH = "biotech"


@dataclass
class TestResult:
    """Result of a single test execution."""
    name: str
    status: TestStatus
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    screenshot_path: Optional[str] = None
    log_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "screenshot_path": self.screenshot_path,
            "log_path": self.log_path,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkMetrics:
    """Metrics collected during benchmarking."""
    load_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    crash_count: int = 0
    fps_average: float = 0.0
    response_time_ms: float = 0.0
    ui_stability_score: float = 100.0
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "load_time": self.load_time,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "crash_count": self.crash_count,
            "fps_average": self.fps_average,
            "response_time_ms": self.response_time_ms,
            "ui_stability_score": self.ui_stability_score,
            "custom_metrics": self.custom_metrics,
        }


class BaseAdapter(ABC):
    """
    Abstract base class for all software adapters.

    Implement this class to create adapters for specific software types
    such as video games, DAWs, web apps, or Windows applications.
    """

    def __init__(self, name: str, software_type: SoftwareType):
        """
        Initialize the adapter.

        Args:
            name: Human-readable name for the adapter.
            software_type: Type of software this adapter handles.
        """
        self.name = name
        self.software_type = software_type
        self._connected = False
        self._config: dict = {}

    @property
    def is_connected(self) -> bool:
        """Check if the adapter is connected to the target."""
        return self._connected

    def configure(self, config: dict) -> None:
        """
        Configure the adapter with custom settings.

        Args:
            config: Dictionary of configuration options.
        """
        self._config.update(config)

    @abstractmethod
    def connect(self, target: str) -> bool:
        """
        Connect to the target application.

        Args:
            target: Path or URL to the target application.

        Returns:
            True if connection successful, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the target application."""
        pass

    @abstractmethod
    def run_test(self, test_name: str, **kwargs: Any) -> TestResult:
        """
        Run a single test.

        Args:
            test_name: Name of the test to run.
            **kwargs: Additional test parameters.

        Returns:
            TestResult with test outcome and metrics.
        """
        pass

    @abstractmethod
    def capture_screenshot(self, filename: str) -> Optional[str]:
        """
        Capture a screenshot of the current state.

        Args:
            filename: Name for the screenshot file.

        Returns:
            Path to the saved screenshot, or None if failed.
        """
        pass

    @abstractmethod
    def collect_metrics(self) -> BenchmarkMetrics:
        """
        Collect current benchmark metrics.

        Returns:
            BenchmarkMetrics with current measurements.
        """
        pass

    def get_logs(self) -> list[str]:
        """
        Retrieve logs from the target application.

        Returns:
            List of log messages.
        """
        return []

    def cleanup(self) -> None:
        """Perform cleanup operations after testing."""
        if self._connected:
            self.disconnect()
