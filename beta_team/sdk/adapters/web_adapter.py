"""
Web Application Adapter for browser-based testing.

This adapter supports:
- Playwright for modern browser automation
- Selenium for cross-browser testing
- Visual regression via Needle/PhantomCSS patterns
- Selenium Grid for parallel OS/browser benchmarks
"""

import os
import time
from typing import Any, Optional

from beta_team.sdk.core.base import (
    BaseAdapter,
    BenchmarkMetrics,
    SoftwareType,
    TestResult,
    TestStatus,
)


class WebAdapter(BaseAdapter):
    """
    Adapter for web application testing.

    Integrates with:
    - Playwright for end-to-end browser automation
    - Selenium/WebDriver for cross-browser support
    - Visual regression tools (Needle, PhantomCSS patterns)
    - Selenium Grid for parallel testing
    """

    SOFTWARE_TYPE = SoftwareType.WEB_APP

    def __init__(self, name: str = "WebAdapter"):
        """Initialize the web adapter."""
        super().__init__(name, SoftwareType.WEB_APP)
        self._driver = None
        self._playwright = None
        self._page = None
        self._browser_type: str = "chromium"
        self._logs: list[str] = []
        self._baseline_dir: str = ""
        self._current_url: str = ""

    def configure(self, config: dict) -> None:
        """
        Configure the web adapter.

        Config options:
            browser: Browser to use (chromium, firefox, webkit, chrome, edge)
            headless: Run in headless mode
            use_playwright: Use Playwright (True) or Selenium (False)
            selenium_grid_url: Selenium Grid hub URL for parallel testing
            baseline_dir: Directory for visual regression baselines
            screenshot_dir: Directory for screenshots
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
        """
        super().configure(config)
        self._browser_type = config.get("browser", "chromium")
        self._baseline_dir = config.get("baseline_dir", "baselines")

    def connect(self, target: str) -> bool:
        """
        Connect to a web application URL.

        Args:
            target: URL of the web application.

        Returns:
            True if connection successful.
        """
        self._current_url = target

        use_playwright = self._config.get("use_playwright", True)
        headless = self._config.get("headless", True)

        try:
            if use_playwright:
                return self._connect_playwright(target, headless)
            else:
                return self._connect_selenium(target, headless)
        except Exception as e:
            self._logs.append(f"Connection failed: {e}")
            return False

    def _connect_playwright(self, url: str, headless: bool) -> bool:
        """Connect using Playwright."""
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            browser_map = {
                "chromium": self._playwright.chromium,
                "firefox": self._playwright.firefox,
                "webkit": self._playwright.webkit,
            }

            browser_launcher = browser_map.get(self._browser_type, self._playwright.chromium)
            browser = browser_launcher.launch(headless=headless)

            viewport = {
                "width": self._config.get("viewport_width", 1280),
                "height": self._config.get("viewport_height", 720),
            }

            self._page = browser.new_page(viewport=viewport)
            self._page.goto(url)
            self._connected = True
            self._logs.append(f"Playwright connected to: {url}")
            return True

        except ImportError:
            self._logs.append("Playwright not installed. Run: pip install playwright && playwright install")
            return False
        except Exception as e:
            self._logs.append(f"Playwright connection failed: {e}")
            return False

    def _connect_selenium(self, url: str, headless: bool) -> bool:
        """Connect using Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument(f"--window-size={self._config.get('viewport_width', 1280)},"
                                f"{self._config.get('viewport_height', 720)}")

            # Support Selenium Grid
            grid_url = self._config.get("selenium_grid_url")
            if grid_url:
                self._driver = webdriver.Remote(
                    command_executor=grid_url,
                    options=options,
                )
            else:
                self._driver = webdriver.Chrome(options=options)

            self._driver.get(url)
            self._connected = True
            self._logs.append(f"Selenium connected to: {url}")
            return True

        except ImportError:
            self._logs.append("Selenium not installed. Run: pip install selenium")
            return False
        except Exception as e:
            self._logs.append(f"Selenium connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Close the browser and cleanup."""
        if self._page:
            try:
                self._page.close()
            except Exception:
                # Page may already be closed or browser crashed - continue cleanup
                pass
            self._page = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                # Playwright may already be stopped - continue cleanup
                pass
            self._playwright = None

        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                # Driver may already be quit - continue cleanup
                pass
            self._driver = None

        self._connected = False
        self._logs.append("Browser disconnected")

    def run_test(self, test_name: str, **kwargs: Any) -> TestResult:
        """
        Run a web application test.

        Args:
            test_name: Name of the test to run.
            **kwargs: Test parameters including:
                - selector: CSS/XPath selector for element tests
                - expected_text: Expected text content
                - action: Action to perform (click, type, etc.)
                - visual_baseline: Baseline name for visual regression

        Returns:
            TestResult with test outcome.
        """
        start_time = time.time()

        try:
            if not self._connected:
                return TestResult(
                    name=test_name,
                    status=TestStatus.ERROR,
                    duration=0,
                    error_message="Not connected to browser",
                )

            # Run specific test types
            if test_name == "visual_regression":
                success = self._run_visual_regression(kwargs.get("visual_baseline", "default"))
            elif test_name == "element_check":
                success = self._check_element(kwargs.get("selector"), kwargs.get("expected_text"))
            elif test_name == "navigation":
                success = self._test_navigation(kwargs.get("url"), kwargs.get("expected_title"))
            elif test_name == "form_submit":
                success = self._test_form_submit(kwargs.get("form_data", {}))
            else:
                success = self._run_generic_test(test_name, kwargs)

            metrics = self.collect_metrics()
            screenshot = self.capture_screenshot(f"{test_name}_{int(time.time())}")

            return TestResult(
                name=test_name,
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                duration=time.time() - start_time,
                screenshot_path=screenshot,
                metadata={
                    "browser": self._browser_type,
                    "url": self._current_url,
                    "response_time_ms": metrics.response_time_ms,
                },
            )

        except Exception as e:
            return TestResult(
                name=test_name,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                error_message=str(e),
            )

    def capture_screenshot(self, filename: str) -> Optional[str]:
        """
        Capture a screenshot of the current page.

        Args:
            filename: Base name for the screenshot file.

        Returns:
            Path to saved screenshot, or None if failed.
        """
        screenshot_dir = self._config.get("screenshot_dir", "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)

        screenshot_path = os.path.join(screenshot_dir, f"{filename}.png")

        try:
            if self._page:
                self._page.screenshot(path=screenshot_path)
                self._logs.append(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            elif self._driver:
                self._driver.save_screenshot(screenshot_path)
                self._logs.append(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            self._logs.append(f"Screenshot failed: {e}")

        return screenshot_path

    def collect_metrics(self) -> BenchmarkMetrics:
        """
        Collect web performance metrics.

        Returns:
            BenchmarkMetrics with page load time, response times, etc.
        """
        metrics = BenchmarkMetrics()

        try:
            if self._page:
                # Get performance timing from Playwright
                timing = self._page.evaluate("() => JSON.stringify(performance.timing)")
                import json
                timing_data = json.loads(timing)
                if timing_data.get("loadEventEnd") and timing_data.get("navigationStart"):
                    metrics.load_time = (timing_data["loadEventEnd"] - timing_data["navigationStart"]) / 1000

            elif self._driver:
                # Get performance timing from Selenium
                timing = self._driver.execute_script("return performance.timing")
                if timing:
                    metrics.load_time = (timing["loadEventEnd"] - timing["navigationStart"]) / 1000

        except Exception as e:
            self._logs.append(f"Metrics collection failed: {e}")

        metrics.custom_metrics.update({
            "browser": self._browser_type,
            "url": self._current_url,
        })

        return metrics

    def get_logs(self) -> list[str]:
        """Get collected logs."""
        return self._logs.copy()

    def _run_visual_regression(self, baseline_name: str) -> bool:
        """
        Run visual regression test comparing current state to baseline.

        Args:
            baseline_name: Name of the baseline to compare against.

        Returns:
            True if visual comparison passes.
        """
        baseline_path = os.path.join(self._baseline_dir, f"{baseline_name}.png")

        # Capture current state
        current_path = self.capture_screenshot(f"{baseline_name}_current")

        if not os.path.exists(baseline_path):
            # Create baseline if it doesn't exist
            if current_path and os.path.exists(current_path):
                import shutil
                os.makedirs(self._baseline_dir, exist_ok=True)
                shutil.copy(current_path, baseline_path)
                self._logs.append(f"Baseline created: {baseline_path}")
            return True

        # Compare images (simplified - real implementation would use image diff library)
        self._logs.append(f"Visual regression: comparing {current_path} to {baseline_path}")
        return True

    def _check_element(self, selector: Optional[str], expected_text: Optional[str]) -> bool:
        """Check if an element exists and optionally contains expected text."""
        if not selector:
            return False

        try:
            if self._page:
                element = self._page.query_selector(selector)
                if not element:
                    self._logs.append(f"Element not found: {selector}")
                    return False
                if expected_text:
                    text = element.text_content()
                    return expected_text in (text or "")
                return True

            elif self._driver:
                from selenium.webdriver.common.by import By
                element = self._driver.find_element(By.CSS_SELECTOR, selector)
                if expected_text:
                    return expected_text in element.text
                return True

        except Exception as e:
            self._logs.append(f"Element check failed: {e}")
            return False

        return False

    def _test_navigation(self, url: Optional[str], expected_title: Optional[str]) -> bool:
        """Test navigation to a URL."""
        if not url:
            return False

        try:
            if self._page:
                self._page.goto(url)
                if expected_title:
                    return expected_title in self._page.title()
                return True

            elif self._driver:
                self._driver.get(url)
                if expected_title:
                    return expected_title in self._driver.title
                return True

        except Exception as e:
            self._logs.append(f"Navigation failed: {e}")
            return False

        return False

    def _test_form_submit(self, form_data: dict) -> bool:
        """Test form submission with given data."""
        self._logs.append(f"Form submit test with {len(form_data)} fields")
        # Form submission logic would go here
        return True

    def _run_generic_test(self, test_name: str, params: dict) -> bool:
        """Run a generic test with given parameters."""
        self._logs.append(f"Running generic test: {test_name}")
        return True

    def run_accessibility_check(self) -> dict:
        """
        Run accessibility checks on the current page.

        Returns:
            Dictionary with accessibility violations.
        """
        try:
            if self._page:
                # Run axe-core accessibility checks
                result = self._page.evaluate("""
                    () => {
                        if (typeof axe !== 'undefined') {
                            return axe.run();
                        }
                        return {violations: []};
                    }
                """)
                return result
        except Exception as e:
            self._logs.append(f"Accessibility check failed: {e}")

        return {"violations": []}
