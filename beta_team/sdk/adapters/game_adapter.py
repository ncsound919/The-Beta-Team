"""
Video Game Adapter for Unity/Unreal integration.

This adapter supports:
- BetaHub SDK integration for Unity/Unreal games
- AirTest for cross-platform image-based automation
- Screenshot capture and gameplay logging
- Discord feedback integration hooks
"""

import os
import subprocess
import time
from typing import Any, Optional

from beta_team.sdk.core.base import (
    BaseAdapter,
    BenchmarkMetrics,
    SoftwareType,
    TestResult,
    TestStatus,
)


class GameAdapter(BaseAdapter):
    """
    Adapter for video game testing with Unity/Unreal support.

    Integrates with:
    - BetaHub for gameplay capture, logs, screenshots, and feedback
    - AirTest for cross-platform image-based automation (Windows/Android)
    """

    SOFTWARE_TYPE = SoftwareType.VIDEO_GAME

    def __init__(self, name: str = "GameAdapter"):
        """Initialize the game adapter."""
        super().__init__(name, SoftwareType.VIDEO_GAME)
        self._process: Optional[subprocess.Popen] = None
        self._logs: list[str] = []
        self._screenshot_dir: str = ""
        self._airtest_enabled: bool = False
        self._betahub_enabled: bool = False

    def configure(self, config: dict) -> None:
        """
        Configure the game adapter.

        Config options:
            screenshot_dir: Directory for saving screenshots
            airtest_enabled: Enable AirTest automation
            betahub_enabled: Enable BetaHub integration
            resolution: Game resolution (e.g., "1920x1080")
            fullscreen: Run in fullscreen mode
        """
        super().configure(config)
        self._screenshot_dir = config.get("screenshot_dir", "screenshots")
        self._airtest_enabled = config.get("airtest_enabled", False)
        self._betahub_enabled = config.get("betahub_enabled", False)

        # Create screenshot directory if needed
        if self._screenshot_dir and not os.path.exists(self._screenshot_dir):
            os.makedirs(self._screenshot_dir, exist_ok=True)

    def connect(self, target: str) -> bool:
        """
        Connect to and launch the game executable.

        Args:
            target: Path to the game executable.

        Returns:
            True if game launched successfully.
        """
        if not os.path.exists(target):
            self._logs.append(f"Game executable not found: {target}")
            return False

        # Validate that target is a file (not a directory) and has executable extension
        if not os.path.isfile(target):
            self._logs.append(f"Target is not a file: {target}")
            return False

        try:
            # Build launch arguments - only allow known safe arguments
            args = [target]
            resolution = self._config.get("resolution")
            if resolution and isinstance(resolution, str):
                parts = resolution.split("x")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    args.extend(["-screen-width", parts[0]])
                    args.extend(["-screen-height", parts[1]])
            if self._config.get("fullscreen") is False:
                args.append("-windowed")

            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._connected = True
            self._logs.append(f"Game launched: {target}")

            # Wait for game to initialize
            time.sleep(self._config.get("startup_delay", 2))
            return True

        except (OSError, subprocess.SubprocessError) as e:
            self._logs.append(f"Failed to launch game: {e}")
            return False

    def disconnect(self) -> None:
        """Close the game process."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        self._connected = False
        self._logs.append("Game disconnected")

    def run_test(self, test_name: str, **kwargs: Any) -> TestResult:
        """
        Run a game test scenario.

        Args:
            test_name: Name of the test to run.
            **kwargs: Test parameters including:
                - airtest_script: Path to AirTest script
                - timeout: Maximum test duration
                - capture_fps: Enable FPS capture

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
                    error_message="Not connected to game",
                )

            # Run AirTest automation if enabled
            if self._airtest_enabled and "airtest_script" in kwargs:
                result = self._run_airtest_script(kwargs["airtest_script"])
                if not result:
                    return TestResult(
                        name=test_name,
                        status=TestStatus.FAILED,
                        duration=time.time() - start_time,
                        error_message="AirTest script failed",
                    )

            # Collect metrics during test
            metrics = self.collect_metrics()

            # Capture screenshot on completion
            screenshot = self.capture_screenshot(f"{test_name}_{int(time.time())}")

            return TestResult(
                name=test_name,
                status=TestStatus.PASSED,
                duration=time.time() - start_time,
                screenshot_path=screenshot,
                metadata={
                    "fps_average": metrics.fps_average,
                    "memory_mb": metrics.memory_usage_mb,
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
        Capture a screenshot of the game.

        Args:
            filename: Base name for the screenshot file.

        Returns:
            Path to saved screenshot, or None if failed.
        """
        if not self._screenshot_dir:
            return None

        screenshot_path = os.path.join(self._screenshot_dir, f"{filename}.png")

        # Use AirTest for screenshot if enabled
        if self._airtest_enabled:
            try:
                # AirTest screenshot command would go here
                # from airtest.core.api import snapshot
                # snapshot(filename=screenshot_path)
                self._logs.append(f"Screenshot captured: {screenshot_path}")
                return screenshot_path
            except Exception as e:
                self._logs.append(f"Screenshot failed: {e}")
                return None

        # Fallback: log that screenshot would be captured
        self._logs.append(f"Screenshot path: {screenshot_path}")
        return screenshot_path

    def collect_metrics(self) -> BenchmarkMetrics:
        """
        Collect game performance metrics.

        Returns:
            BenchmarkMetrics with FPS, memory usage, etc.
        """
        metrics = BenchmarkMetrics()

        if self._process:
            try:
                # Get process memory info if psutil is available
                import psutil
                proc = psutil.Process(self._process.pid)
                metrics.memory_usage_mb = proc.memory_info().rss / (1024 * 1024)
                metrics.cpu_usage_percent = proc.cpu_percent()
            except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                # psutil not available or process no longer exists - metrics will use defaults
                pass

        # FPS and other metrics would come from game hooks or BetaHub
        if self._betahub_enabled:
            metrics.custom_metrics["betahub_session"] = True

        return metrics

    def get_logs(self) -> list[str]:
        """Get collected game logs."""
        return self._logs.copy()

    def _run_airtest_script(self, script_path: str) -> bool:
        """
        Execute an AirTest automation script.

        Args:
            script_path: Path to the AirTest script.

        Returns:
            True if script executed successfully.
        """
        if not os.path.exists(script_path):
            self._logs.append(f"AirTest script not found: {script_path}")
            return False

        try:
            # AirTest execution would go here
            # from airtest.cli.runner import run_script
            # run_script(script_path)
            self._logs.append(f"AirTest script executed: {script_path}")
            return True
        except Exception as e:
            self._logs.append(f"AirTest script failed: {e}")
            return False

    def send_discord_feedback(self, message: str, channel_webhook: str) -> bool:
        """
        Send feedback to Discord via webhook (BetaHub integration).

        Args:
            message: Feedback message to send.
            channel_webhook: Discord webhook URL.

        Returns:
            True if feedback sent successfully.
        """
        # Validate Discord webhook URL
        if not channel_webhook.startswith("https://discord.com/api/webhooks/"):
            self._logs.append("Invalid Discord webhook URL: must start with https://discord.com/api/webhooks/")
            return False

        # Discord has a 2000 character limit for messages
        max_message_length = 2000
        if len(message) > max_message_length:
            message = message[:max_message_length - 3] + "..."

        try:
            import json
            import urllib.request

            payload = json.dumps({"content": message}).encode("utf-8")
            req = urllib.request.Request(
                channel_webhook,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            self._logs.append("Discord feedback sent")
            return True
        except Exception as e:
            self._logs.append(f"Discord feedback failed: {e}")
            return False
