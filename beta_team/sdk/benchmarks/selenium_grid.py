"""
Selenium Grid Benchmark Integration.

Provides parallel OS/browser benchmarking capabilities using Selenium Grid
for distributed testing across multiple environments.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GridBenchmarkResult:
    """Result from a single grid node benchmark."""
    browser: str
    platform: str
    node_id: str
    success: bool
    duration_ms: float
    load_time_ms: float = 0.0
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "browser": self.browser,
            "platform": self.platform,
            "node_id": self.node_id,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "load_time_ms": self.load_time_ms,
            "screenshot_path": self.screenshot_path,
            "error": self.error,
            "custom_metrics": self.custom_metrics,
        }


@dataclass
class GridMetrics:
    """Aggregated metrics from grid benchmarking."""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    avg_duration_ms: float = 0.0
    avg_load_time_ms: float = 0.0
    nodes_used: int = 0
    browsers_tested: list = field(default_factory=list)
    platforms_tested: list = field(default_factory=list)
    results: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "avg_duration_ms": self.avg_duration_ms,
            "avg_load_time_ms": self.avg_load_time_ms,
            "nodes_used": self.nodes_used,
            "browsers_tested": self.browsers_tested,
            "platforms_tested": self.platforms_tested,
            "results": [r.to_dict() for r in self.results],
        }


class SeleniumGridBenchmark:
    """
    Benchmark runner for Selenium Grid-based parallel testing.

    Provides distributed benchmarking across:
    - Multiple browsers (Chrome, Firefox, Edge, Safari)
    - Multiple operating systems (Windows, macOS, Linux)
    - Parallel execution for faster benchmarks
    """

    # Default browser configurations for grid testing
    DEFAULT_CONFIGS = [
        {"browser": "chrome", "platform": "windows"},
        {"browser": "chrome", "platform": "linux"},
        {"browser": "firefox", "platform": "windows"},
        {"browser": "firefox", "platform": "linux"},
        {"browser": "edge", "platform": "windows"},
    ]

    def __init__(self, hub_url: str = "http://localhost:4444/wd/hub"):
        """
        Initialize the grid benchmark runner.

        Args:
            hub_url: Selenium Grid hub URL.
        """
        self.hub_url = hub_url
        self._metrics = GridMetrics()
        self._logs: list[str] = []
        self._max_workers = 5

    def set_max_workers(self, workers: int) -> None:
        """Set maximum parallel workers."""
        self._max_workers = workers

    def run_benchmark(self, url: str, configs: Optional[list[dict]] = None, timeout: int = 30) -> GridMetrics:
        """
        Run parallel benchmarks across multiple browser/OS configurations.

        Args:
            url: URL to benchmark.
            configs: List of configurations. Each dict should have 'browser' and 'platform'.
                    If None, uses DEFAULT_CONFIGS.
            timeout: Timeout per test in seconds.

        Returns:
            GridMetrics with aggregated results.
        """
        if configs is None:
            configs = self.DEFAULT_CONFIGS

        self._metrics = GridMetrics()
        results = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {}
            for idx, config in enumerate(configs):
                future = executor.submit(
                    self._run_single_benchmark,
                    url,
                    config["browser"],
                    config.get("platform", "any"),
                    f"node_{idx}",
                    timeout,
                )
                futures[future] = config

            for future in as_completed(futures):
                config = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(GridBenchmarkResult(
                        browser=config["browser"],
                        platform=config.get("platform", "any"),
                        node_id="error",
                        success=False,
                        duration_ms=0,
                        error=str(e),
                    ))

        # Aggregate metrics
        self._metrics.total_tests = len(results)
        self._metrics.passed_tests = sum(1 for r in results if r.success)
        self._metrics.failed_tests = self._metrics.total_tests - self._metrics.passed_tests
        self._metrics.results = results

        if results:
            durations = [r.duration_ms for r in results if r.success]
            load_times = [r.load_time_ms for r in results if r.success and r.load_time_ms > 0]
            if durations:
                self._metrics.avg_duration_ms = sum(durations) / len(durations)
            if load_times:
                self._metrics.avg_load_time_ms = sum(load_times) / len(load_times)

        self._metrics.nodes_used = len(set(r.node_id for r in results))
        self._metrics.browsers_tested = list(set(r.browser for r in results))
        self._metrics.platforms_tested = list(set(r.platform for r in results))

        self._logs.append(f"Grid benchmark complete: {self._metrics.passed_tests}/{self._metrics.total_tests} passed")
        return self._metrics

    def _run_single_benchmark(self, url: str, browser: str, platform: str, node_id: str, timeout: int) -> GridBenchmarkResult:
        """
        Run a single benchmark on one grid node.

        Args:
            url: URL to benchmark.
            browser: Browser name.
            platform: Platform name.
            node_id: Identifier for the node.
            timeout: Timeout in seconds.

        Returns:
            GridBenchmarkResult for this test.
        """
        start = time.time()
        driver = None

        try:
            from selenium import webdriver
            from selenium.webdriver.common.options import ArgOptions

            # Create capabilities
            options = ArgOptions()
            options.set_capability("browserName", browser)
            if platform != "any":
                options.set_capability("platformName", platform)

            driver = webdriver.Remote(
                command_executor=self.hub_url,
                options=options,
            )
            driver.set_page_load_timeout(timeout)

            # Measure page load
            load_start = time.time()
            driver.get(url)
            load_time = (time.time() - load_start) * 1000

            # Get actual node info if available
            actual_node = driver.capabilities.get("se:nodeId", node_id)

            duration = (time.time() - start) * 1000

            return GridBenchmarkResult(
                browser=browser,
                platform=platform,
                node_id=actual_node,
                success=True,
                duration_ms=duration,
                load_time_ms=load_time,
            )

        except ImportError:
            return GridBenchmarkResult(
                browser=browser,
                platform=platform,
                node_id=node_id,
                success=False,
                duration_ms=(time.time() - start) * 1000,
                error="Selenium not installed",
            )
        except Exception as e:
            return GridBenchmarkResult(
                browser=browser,
                platform=platform,
                node_id=node_id,
                success=False,
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def check_grid_status(self) -> dict:
        """
        Check Selenium Grid hub status.

        Returns:
            Dictionary with grid status information.
        """
        try:
            import urllib.request
            import json

            status_url = self.hub_url.replace("/wd/hub", "/status")
            response = urllib.request.urlopen(status_url, timeout=5)
            data = json.loads(response.read().decode())

            return {
                "ready": data.get("value", {}).get("ready", False),
                "message": data.get("value", {}).get("message", "Unknown"),
                "nodes": data.get("value", {}).get("nodes", []),
            }

        except Exception as e:
            self._logs.append(f"Grid status check failed: {e}")
            return {"ready": False, "error": str(e)}

    def get_available_capabilities(self) -> list[dict]:
        """
        Get available browser/platform capabilities from the grid.

        Returns:
            List of available capability combinations.
        """
        status = self.check_grid_status()
        capabilities = []

        for node in status.get("nodes", []):
            for slot in node.get("slots", []):
                stereotype = slot.get("stereotype", {})
                capabilities.append({
                    "browser": stereotype.get("browserName", "unknown"),
                    "platform": stereotype.get("platformName", "any"),
                    "version": stereotype.get("browserVersion", ""),
                })

        return capabilities

    def compare_browsers(self, url: str, browsers: list[str]) -> dict:
        """
        Compare performance across different browsers.

        Args:
            url: URL to benchmark.
            browsers: List of browser names to compare.

        Returns:
            Dictionary with browser comparison results.
        """
        configs = [{"browser": b, "platform": "any"} for b in browsers]
        metrics = self.run_benchmark(url, configs)

        comparison = {}
        for result in metrics.results:
            if result.success:
                comparison[result.browser] = {
                    "load_time_ms": result.load_time_ms,
                    "duration_ms": result.duration_ms,
                }

        return comparison

    def compare_platforms(self, url: str, browser: str, platforms: list[str]) -> dict:
        """
        Compare performance across different platforms for a single browser.

        Args:
            url: URL to benchmark.
            browser: Browser to use.
            platforms: List of platform names to compare.

        Returns:
            Dictionary with platform comparison results.
        """
        configs = [{"browser": browser, "platform": p} for p in platforms]
        metrics = self.run_benchmark(url, configs)

        comparison = {}
        for result in metrics.results:
            if result.success:
                comparison[result.platform] = {
                    "load_time_ms": result.load_time_ms,
                    "duration_ms": result.duration_ms,
                }

        return comparison

    def get_metrics(self) -> GridMetrics:
        """Get collected metrics."""
        return self._metrics

    def get_logs(self) -> list[str]:
        """Get benchmark logs."""
        return self._logs.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = GridMetrics()
        self._logs.clear()
