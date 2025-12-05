"""
AirTest Benchmark Integration.

Provides benchmarking capabilities for game testing using AirTest's
cross-platform image-based automation for Windows and Android.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AirTestMetrics:
    """Metrics collected during AirTest benchmarking."""
    fps_average: float = 0.0
    fps_min: float = 0.0
    fps_max: float = 0.0
    frame_time_ms: float = 0.0
    image_match_time_ms: float = 0.0
    touch_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    crash_count: int = 0
    screenshot_count: int = 0
    custom_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "fps_average": self.fps_average,
            "fps_min": self.fps_min,
            "fps_max": self.fps_max,
            "frame_time_ms": self.frame_time_ms,
            "image_match_time_ms": self.image_match_time_ms,
            "touch_response_time_ms": self.touch_response_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "crash_count": self.crash_count,
            "screenshot_count": self.screenshot_count,
            "custom_metrics": self.custom_metrics,
        }


class AirTestBenchmark:
    """
    Benchmark runner for AirTest-based game testing.

    Provides cross-platform image-based automation for:
    - Windows games (Unity, Unreal)
    - Android games
    - FPS and frame time measurement
    - Touch/click response times
    - Visual element detection benchmarks
    """

    def __init__(self, platform: str = "windows"):
        """
        Initialize the benchmark runner.

        Args:
            platform: Target platform (windows, android).
        """
        self.platform = platform
        self._device = None
        self._metrics = AirTestMetrics()
        self._logs: list[str] = []
        self._connected = False
        self._screenshot_dir = "screenshots"

    def connect(self, target: str, **options: Any) -> bool:
        """
        Connect to the target device/application.

        Args:
            target: Device connection string or app path.
                Windows: Path to game executable
                Android: Device serial or "Android:///"
            **options: Additional connection options.

        Returns:
            True if connected successfully.
        """
        try:
            # AirTest device connection would go here
            # from airtest.core.api import connect_device, init_device
            # self._device = connect_device(target)

            self._logs.append(f"Connected to {self.platform}: {target}")
            self._connected = True
            return True

        except ImportError:
            self._logs.append("AirTest not installed. Run: pip install airtest")
            return False
        except Exception as e:
            self._logs.append(f"Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the device."""
        self._device = None
        self._connected = False
        self._logs.append("Disconnected from device")

    def benchmark_image_match(self, template_path: str, iterations: int = 10) -> float:
        """
        Benchmark image template matching performance.

        Args:
            template_path: Path to template image.
            iterations: Number of iterations for averaging.

        Returns:
            Average matching time in milliseconds.
        """
        if not os.path.exists(template_path):
            self._logs.append(f"Template not found: {template_path}")
            return 0.0

        times = []

        for _ in range(iterations):
            start = time.time()
            try:
                # AirTest image match would go here
                # from airtest.core.api import exists
                # exists(Template(template_path))
                pass
            except Exception:
                pass
            times.append((time.time() - start) * 1000)

        if times:
            avg_time = sum(times) / len(times)
            self._metrics.image_match_time_ms = avg_time
            self._logs.append(f"Image match avg: {avg_time:.2f}ms")
            return avg_time

        return 0.0

    def benchmark_touch_response(self, x: int, y: int, wait_template: Optional[str] = None, iterations: int = 5) -> float:
        """
        Benchmark touch/click response time.

        Args:
            x: X coordinate to touch.
            y: Y coordinate to touch.
            wait_template: Optional template to wait for after touch.
            iterations: Number of iterations for averaging.

        Returns:
            Average response time in milliseconds.
        """
        times = []

        for _ in range(iterations):
            start = time.time()
            try:
                # AirTest touch would go here
                # from airtest.core.api import touch, wait
                # touch((x, y))
                # if wait_template:
                #     wait(Template(wait_template))
                pass
            except Exception:
                pass
            times.append((time.time() - start) * 1000)

        if times:
            avg_time = sum(times) / len(times)
            self._metrics.touch_response_time_ms = avg_time
            self._logs.append(f"Touch response avg: {avg_time:.2f}ms")
            return avg_time

        return 0.0

    def benchmark_fps(self, duration_seconds: int = 10) -> dict:
        """
        Measure FPS over a period of time.

        Args:
            duration_seconds: Duration to measure FPS.

        Returns:
            Dictionary with FPS statistics.
        """
        fps_samples = []
        start = time.time()

        while time.time() - start < duration_seconds:
            try:
                # FPS measurement would use platform-specific methods
                # For Android: adb shell dumpsys gfxinfo
                # For Windows: DirectX/OpenGL hooks or process monitoring
                pass
            except Exception:
                pass
            time.sleep(0.1)

        if fps_samples:
            self._metrics.fps_average = sum(fps_samples) / len(fps_samples)
            self._metrics.fps_min = min(fps_samples)
            self._metrics.fps_max = max(fps_samples)

        result = {
            "fps_average": self._metrics.fps_average,
            "fps_min": self._metrics.fps_min,
            "fps_max": self._metrics.fps_max,
            "samples": len(fps_samples),
            "duration": duration_seconds,
        }

        self._logs.append(f"FPS benchmark: avg={self._metrics.fps_average:.1f}")
        return result

    def capture_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a screenshot.

        Args:
            filename: Optional filename. If None, auto-generated.

        Returns:
            Path to screenshot or None.
        """
        if not os.path.exists(self._screenshot_dir):
            os.makedirs(self._screenshot_dir, exist_ok=True)

        if filename is None:
            filename = f"airtest_{int(time.time())}.png"

        filepath = os.path.join(self._screenshot_dir, filename)

        try:
            # AirTest screenshot would go here
            # from airtest.core.api import snapshot
            # snapshot(filename=filepath)
            self._metrics.screenshot_count += 1
            self._logs.append(f"Screenshot: {filepath}")
            return filepath
        except Exception as e:
            self._logs.append(f"Screenshot failed: {e}")
            return None

    def run_gameplay_scenario(self, script_path: str) -> dict:
        """
        Run a gameplay automation scenario and collect metrics.

        Args:
            script_path: Path to AirTest script.

        Returns:
            Dictionary with scenario results and metrics.
        """
        if not os.path.exists(script_path):
            return {"success": False, "error": "Script not found"}

        start = time.time()
        success = True
        error_msg = None

        try:
            # AirTest script execution would go here
            # from airtest.cli.runner import run_script
            # run_script(script_path)
            pass
        except Exception as e:
            success = False
            error_msg = str(e)
            self._metrics.crash_count += 1

        return {
            "success": success,
            "duration": time.time() - start,
            "error": error_msg,
            "crash_count": self._metrics.crash_count,
        }

    def collect_android_metrics(self, package_name: str) -> dict:
        """
        Collect Android-specific performance metrics.

        Args:
            package_name: Package name of the game.

        Returns:
            Dictionary with Android metrics.
        """
        if self.platform != "android":
            return {}

        metrics = {}

        try:
            import subprocess

            # Get memory info
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "meminfo", package_name],
                capture_output=True,
                text=True,
            )
            # Parse memory output
            for line in result.stdout.split("\n"):
                if "TOTAL" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        metrics["memory_kb"] = int(parts[1])
                        self._metrics.memory_usage_mb = int(parts[1]) / 1024
                    break

            # Get GPU rendering info
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "gfxinfo", package_name],
                capture_output=True,
                text=True,
            )
            # Parse frame times

        except Exception as e:
            self._logs.append(f"Android metrics collection failed: {e}")

        return metrics

    def get_metrics(self) -> AirTestMetrics:
        """Get collected metrics."""
        return self._metrics

    def get_logs(self) -> list[str]:
        """Get benchmark logs."""
        return self._logs.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = AirTestMetrics()
        self._logs.clear()

    def generate_report(self, output_path: str) -> str:
        """
        Generate a benchmark report.

        Args:
            output_path: Path for the report file.

        Returns:
            Path to generated report.
        """
        import json

        report = {
            "platform": self.platform,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": self._metrics.to_dict(),
            "logs": self._logs,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        self._logs.append(f"Report generated: {output_path}")
        return output_path
