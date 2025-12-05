"""
WinAppDriver Benchmark Integration.

Provides benchmarking capabilities for Windows desktop applications
using WinAppDriver for UI automation and metrics collection.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class WinAppDriverMetrics:
    """Metrics collected during WinAppDriver benchmarking."""
    load_time_ms: float = 0.0
    ui_response_time_ms: float = 0.0
    crash_count: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    element_find_time_ms: float = 0.0
    action_execution_time_ms: float = 0.0
    screenshot_count: int = 0
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "load_time_ms": self.load_time_ms,
            "ui_response_time_ms": self.ui_response_time_ms,
            "crash_count": self.crash_count,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "element_find_time_ms": self.element_find_time_ms,
            "action_execution_time_ms": self.action_execution_time_ms,
            "screenshot_count": self.screenshot_count,
            "custom_metrics": self.custom_metrics,
        }


class WinAppDriverBenchmark:
    """
    Benchmark runner for WinAppDriver-based testing.

    Provides scripted benchmarks for:
    - Load times
    - UI response times
    - Crash detection
    - Memory and CPU usage
    - UI stability metrics
    """

    def __init__(self, server_url: str = "http://127.0.0.1:4723"):
        """
        Initialize the benchmark runner.

        Args:
            server_url: WinAppDriver server URL.
        """
        self.server_url = server_url
        self._session = None
        self._metrics = WinAppDriverMetrics()
        self._logs: list[str] = []
        self._start_time: Optional[float] = None

    def start_session(self, app_path: str, **capabilities: Any) -> bool:
        """
        Start a WinAppDriver session for the application.

        Args:
            app_path: Path to the application executable.
            **capabilities: Additional WinAppDriver capabilities.

        Returns:
            True if session started successfully.
        """
        self._start_time = time.time()

        try:
            from selenium import webdriver
            from selenium.webdriver.common.options import ArgOptions

            options = ArgOptions()
            options.set_capability("app", app_path)
            options.set_capability("platformName", "Windows")
            options.set_capability("deviceName", "WindowsPC")

            for key, value in capabilities.items():
                options.set_capability(key, value)

            self._session = webdriver.Remote(
                command_executor=self.server_url,
                options=options,
            )

            self._metrics.load_time_ms = (time.time() - self._start_time) * 1000
            self._logs.append(f"Session started. Load time: {self._metrics.load_time_ms:.2f}ms")
            return True

        except ImportError:
            self._logs.append("Selenium not installed")
            return False
        except Exception as e:
            self._logs.append(f"Failed to start session: {e}")
            return False

    def end_session(self) -> None:
        """End the WinAppDriver session."""
        if self._session:
            try:
                self._session.quit()
            except Exception:
                pass
            self._session = None
        self._logs.append("Session ended")

    def benchmark_element_find(self, locator_strategy: str, locator_value: str, iterations: int = 10) -> float:
        """
        Benchmark element finding performance.

        Args:
            locator_strategy: Strategy to use (xpath, id, name, etc.).
            locator_value: Locator value.
            iterations: Number of iterations for averaging.

        Returns:
            Average time in milliseconds.
        """
        if not self._session:
            return 0.0

        from selenium.webdriver.common.by import By

        strategy_map = {
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
        }

        by = strategy_map.get(locator_strategy, By.XPATH)
        times = []

        for _ in range(iterations):
            start = time.time()
            try:
                self._session.find_element(by, locator_value)
                times.append((time.time() - start) * 1000)
            except Exception:
                pass

        if times:
            avg_time = sum(times) / len(times)
            self._metrics.element_find_time_ms = avg_time
            self._logs.append(f"Element find avg: {avg_time:.2f}ms over {len(times)} iterations")
            return avg_time

        return 0.0

    def benchmark_action_execution(self, element_id: str, action: str, iterations: int = 10) -> float:
        """
        Benchmark UI action execution performance.

        Args:
            element_id: AutomationId of the element.
            action: Action to perform (click, type, etc.).
            iterations: Number of iterations for averaging.

        Returns:
            Average time in milliseconds.
        """
        if not self._session:
            return 0.0

        from selenium.webdriver.common.by import By

        times = []

        for _ in range(iterations):
            try:
                element = self._session.find_element(
                    By.XPATH, f"//*[@AutomationId='{element_id}']"
                )

                start = time.time()
                if action == "click":
                    element.click()
                elif action == "type":
                    element.send_keys("benchmark")
                    element.clear()

                times.append((time.time() - start) * 1000)

            except Exception:
                pass

        if times:
            avg_time = sum(times) / len(times)
            self._metrics.action_execution_time_ms = avg_time
            self._logs.append(f"Action execution avg: {avg_time:.2f}ms")
            return avg_time

        return 0.0

    def benchmark_ui_response(self, trigger_element: str, response_element: str, timeout: float = 5.0) -> float:
        """
        Benchmark UI response time after triggering an action.

        Args:
            trigger_element: AutomationId of trigger element.
            response_element: AutomationId of response element to wait for.
            timeout: Maximum wait time in seconds.

        Returns:
            Response time in milliseconds.
        """
        if not self._session:
            return 0.0

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            trigger = self._session.find_element(
                By.XPATH, f"//*[@AutomationId='{trigger_element}']"
            )

            start = time.time()
            trigger.click()

            WebDriverWait(self._session, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[@AutomationId='{response_element}']")
                )
            )

            response_time = (time.time() - start) * 1000
            self._metrics.ui_response_time_ms = response_time
            self._logs.append(f"UI response time: {response_time:.2f}ms")
            return response_time

        except Exception as e:
            self._logs.append(f"UI response benchmark failed: {e}")
            return timeout * 1000

    def capture_screenshot(self, filename: str) -> Optional[str]:
        """
        Capture a screenshot during benchmarking.

        Args:
            filename: Name for the screenshot file.

        Returns:
            Path to screenshot or None.
        """
        if not self._session:
            return None

        try:
            self._session.get_screenshot_as_file(filename)
            self._metrics.screenshot_count += 1
            return filename
        except Exception as e:
            self._logs.append(f"Screenshot failed: {e}")
            return None

    def collect_system_metrics(self, pid: Optional[int] = None) -> dict:
        """
        Collect system-level metrics for the application.

        Args:
            pid: Process ID to monitor. If None, tries to get from session.

        Returns:
            Dictionary of system metrics.
        """
        try:
            import psutil

            if pid is None and self._session:
                # Try to get PID from session
                pass

            if pid:
                proc = psutil.Process(pid)
                self._metrics.memory_usage_mb = proc.memory_info().rss / (1024 * 1024)
                self._metrics.cpu_usage_percent = proc.cpu_percent(interval=0.1)

                return {
                    "memory_mb": self._metrics.memory_usage_mb,
                    "cpu_percent": self._metrics.cpu_usage_percent,
                }

        except (ImportError, Exception) as e:
            self._logs.append(f"System metrics collection failed: {e}")

        return {}

    def run_stability_benchmark(self, duration_seconds: int = 60) -> dict:
        """
        Run a stability benchmark over time.

        Args:
            duration_seconds: Duration of the benchmark.

        Returns:
            Dictionary with stability metrics.
        """
        start = time.time()
        samples = []
        crash_detected = False

        while time.time() - start < duration_seconds:
            try:
                # Check if session is still responsive
                self._session.title
                metrics = self.collect_system_metrics()
                samples.append(metrics)
            except Exception:
                crash_detected = True
                self._metrics.crash_count += 1
                break

            time.sleep(1)

        return {
            "duration_seconds": time.time() - start,
            "samples": len(samples),
            "crash_detected": crash_detected,
            "crash_count": self._metrics.crash_count,
        }

    def get_metrics(self) -> WinAppDriverMetrics:
        """Get collected metrics."""
        return self._metrics

    def get_logs(self) -> list[str]:
        """Get benchmark logs."""
        return self._logs.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = WinAppDriverMetrics()
        self._logs.clear()
