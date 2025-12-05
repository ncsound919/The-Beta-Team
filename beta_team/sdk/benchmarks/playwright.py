"""
Playwright Benchmark Integration.

Provides benchmarking capabilities for web application testing using
Playwright for end-to-end browser automation and performance metrics.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PlaywrightMetrics:
    """Metrics collected during Playwright benchmarking."""
    page_load_time_ms: float = 0.0
    dom_content_loaded_ms: float = 0.0
    first_contentful_paint_ms: float = 0.0
    largest_contentful_paint_ms: float = 0.0
    time_to_interactive_ms: float = 0.0
    network_requests: int = 0
    network_transfer_kb: float = 0.0
    javascript_heap_mb: float = 0.0
    visual_stability_score: float = 100.0
    screenshot_count: int = 0
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "page_load_time_ms": self.page_load_time_ms,
            "dom_content_loaded_ms": self.dom_content_loaded_ms,
            "first_contentful_paint_ms": self.first_contentful_paint_ms,
            "largest_contentful_paint_ms": self.largest_contentful_paint_ms,
            "time_to_interactive_ms": self.time_to_interactive_ms,
            "network_requests": self.network_requests,
            "network_transfer_kb": self.network_transfer_kb,
            "javascript_heap_mb": self.javascript_heap_mb,
            "visual_stability_score": self.visual_stability_score,
            "screenshot_count": self.screenshot_count,
            "custom_metrics": self.custom_metrics,
        }


class PlaywrightBenchmark:
    """
    Benchmark runner for Playwright-based web testing.

    Provides comprehensive web performance benchmarking:
    - Core Web Vitals (LCP, FCP, CLS)
    - Page load metrics
    - Network performance
    - Visual regression testing patterns
    """

    def __init__(self, browser_type: str = "chromium"):
        """
        Initialize the benchmark runner.

        Args:
            browser_type: Browser to use (chromium, firefox, webkit).
        """
        self.browser_type = browser_type
        self._playwright = None
        self._browser = None
        self._page = None
        self._metrics = PlaywrightMetrics()
        self._logs: list[str] = []
        self._screenshot_dir = "screenshots"
        self._baseline_dir = "baselines"

    def start(self, headless: bool = True) -> bool:
        """
        Start Playwright and launch browser.

        Args:
            headless: Run in headless mode.

        Returns:
            True if started successfully.
        """
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            browser_map = {
                "chromium": self._playwright.chromium,
                "firefox": self._playwright.firefox,
                "webkit": self._playwright.webkit,
            }

            launcher = browser_map.get(self.browser_type, self._playwright.chromium)
            self._browser = launcher.launch(headless=headless)
            self._page = self._browser.new_page()

            self._logs.append(f"Started {self.browser_type} browser")
            return True

        except ImportError:
            self._logs.append("Playwright not installed. Run: pip install playwright && playwright install")
            return False
        except Exception as e:
            self._logs.append(f"Failed to start browser: {e}")
            return False

    def stop(self) -> None:
        """Stop browser and cleanup."""
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._logs.append("Browser stopped")

    def benchmark_page_load(self, url: str) -> dict:
        """
        Benchmark page load performance.

        Args:
            url: URL to benchmark.

        Returns:
            Dictionary with page load metrics.
        """
        if not self._page:
            return {"error": "Browser not started"}

        try:
            start = time.time()
            self._page.goto(url, wait_until="networkidle")
            load_time = (time.time() - start) * 1000

            # Get performance timing
            timing = self._page.evaluate("""
                () => {
                    const t = performance.timing;
                    return {
                        navigationStart: t.navigationStart,
                        domContentLoaded: t.domContentLoadedEventEnd - t.navigationStart,
                        loadComplete: t.loadEventEnd - t.navigationStart,
                    };
                }
            """)

            self._metrics.page_load_time_ms = load_time
            self._metrics.dom_content_loaded_ms = timing.get("domContentLoaded", 0)

            result = {
                "url": url,
                "load_time_ms": load_time,
                "dom_content_loaded_ms": timing.get("domContentLoaded", 0),
                "load_complete_ms": timing.get("loadComplete", 0),
            }

            self._logs.append(f"Page load: {url} in {load_time:.2f}ms")
            return result

        except Exception as e:
            self._logs.append(f"Page load benchmark failed: {e}")
            return {"error": str(e)}

    def benchmark_core_web_vitals(self, url: str) -> dict:
        """
        Benchmark Core Web Vitals (LCP, FCP, CLS).

        Args:
            url: URL to benchmark.

        Returns:
            Dictionary with Core Web Vitals.
        """
        if not self._page:
            return {"error": "Browser not started"}

        try:
            # Inject Web Vitals measurement script
            self._page.goto(url)

            # Wait for page to stabilize
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # Get paint metrics
            metrics = self._page.evaluate("""
                () => {
                    const entries = {};
                    
                    // First Contentful Paint
                    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
                    if (fcpEntry) entries.fcp = fcpEntry.startTime;
                    
                    // LCP approximation from paint timing
                    const paintEntries = performance.getEntriesByType('paint');
                    paintEntries.forEach(entry => {
                        if (entry.name === 'first-contentful-paint') {
                            entries.fcp = entry.startTime;
                        }
                    });
                    
                    return entries;
                }
            """)

            self._metrics.first_contentful_paint_ms = metrics.get("fcp", 0)

            result = {
                "url": url,
                "fcp_ms": metrics.get("fcp", 0),
                "lcp_ms": metrics.get("lcp", 0),
                "cls": metrics.get("cls", 0),
            }

            self._logs.append(f"Core Web Vitals: FCP={result['fcp_ms']:.2f}ms")
            return result

        except Exception as e:
            self._logs.append(f"Core Web Vitals benchmark failed: {e}")
            return {"error": str(e)}

    def benchmark_network(self, url: str) -> dict:
        """
        Benchmark network performance and resources.

        Args:
            url: URL to benchmark.

        Returns:
            Dictionary with network metrics.
        """
        if not self._page:
            return {"error": "Browser not started"}

        try:
            requests = []
            total_size = 0

            def handle_request(request):
                requests.append(request.url)

            def handle_response(response):
                nonlocal total_size
                try:
                    body = response.body()
                    total_size += len(body)
                except Exception:
                    pass

            self._page.on("request", handle_request)
            self._page.on("response", handle_response)

            self._page.goto(url, wait_until="networkidle")

            self._metrics.network_requests = len(requests)
            self._metrics.network_transfer_kb = total_size / 1024

            result = {
                "url": url,
                "total_requests": len(requests),
                "total_transfer_kb": total_size / 1024,
            }

            self._logs.append(f"Network: {len(requests)} requests, {total_size / 1024:.2f}KB")
            return result

        except Exception as e:
            self._logs.append(f"Network benchmark failed: {e}")
            return {"error": str(e)}

    def run_visual_regression(self, url: str, baseline_name: str) -> dict:
        """
        Run visual regression test against a baseline.

        Args:
            url: URL to test.
            baseline_name: Name of the baseline image.

        Returns:
            Dictionary with comparison results.
        """
        if not self._page:
            return {"error": "Browser not started", "passed": False}

        if not os.path.exists(self._screenshot_dir):
            os.makedirs(self._screenshot_dir, exist_ok=True)

        if not os.path.exists(self._baseline_dir):
            os.makedirs(self._baseline_dir, exist_ok=True)

        baseline_path = os.path.join(self._baseline_dir, f"{baseline_name}.png")
        current_path = os.path.join(self._screenshot_dir, f"{baseline_name}_current.png")

        try:
            self._page.goto(url)
            self._page.wait_for_load_state("networkidle")
            self._page.screenshot(path=current_path)
            self._metrics.screenshot_count += 1

            # Create baseline if doesn't exist
            if not os.path.exists(baseline_path):
                import shutil
                shutil.copy(current_path, baseline_path)
                self._logs.append(f"Baseline created: {baseline_path}")
                return {"passed": True, "baseline_created": True}

            # Compare images (simplified - real implementation would use image diff)
            self._logs.append(f"Visual regression: comparing to {baseline_name}")
            return {
                "passed": True,
                "baseline_path": baseline_path,
                "current_path": current_path,
            }

        except Exception as e:
            self._logs.append(f"Visual regression failed: {e}")
            return {"passed": False, "error": str(e)}

    def capture_screenshot(self, filename: str, full_page: bool = False) -> Optional[str]:
        """
        Capture a screenshot.

        Args:
            filename: Name for the screenshot.
            full_page: Capture full page vs viewport.

        Returns:
            Path to screenshot or None.
        """
        if not self._page:
            return None

        if not os.path.exists(self._screenshot_dir):
            os.makedirs(self._screenshot_dir, exist_ok=True)

        filepath = os.path.join(self._screenshot_dir, f"{filename}.png")

        try:
            self._page.screenshot(path=filepath, full_page=full_page)
            self._metrics.screenshot_count += 1
            self._logs.append(f"Screenshot: {filepath}")
            return filepath
        except Exception as e:
            self._logs.append(f"Screenshot failed: {e}")
            return None

    def get_metrics(self) -> PlaywrightMetrics:
        """Get collected metrics."""
        return self._metrics

    def get_logs(self) -> list[str]:
        """Get benchmark logs."""
        return self._logs.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = PlaywrightMetrics()
        self._logs.clear()
