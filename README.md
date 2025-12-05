# The-Beta-Team
Agentic Software Beta Testing 

## Beta Team Launcher v2.0

Enhanced UI/UX with menu bar, Go/Stop buttons, status bar for professional beta testing.

Agentic Software Beta Testing - Local open-source beta testing dashboard for desktop/web apps with menu toggles, benchmarks, and deltas.

## Modular SDK Architecture

Beta Team provides a modular SDK for deep integration into diverse software:

- **Video Games**: Unity/Unreal SDKs with BetaHub integration, AirTest for cross-platform automation
- **VST Plugins/DAWs**: VST3/AU/CLAP testing, WinAppDriver for DAW UI automation
- **Web Apps**: Playwright/Selenium for browser automation, visual regression testing
- **Windows Software**: WinAppDriver/Winium for WPF/WinForms/UWP automation
- **Biotech/Fintech**: Specialized adapters for regulated software testing

### SDK Quick Start

```python
from beta_team.sdk import BaseAdapter, AdapterRegistry
from beta_team.sdk.adapters import GameAdapter, WebAdapter, WindowsAdapter, VSTAdapter
from beta_team.sdk.benchmarks import WinAppDriverBenchmark, AirTestBenchmark, PlaywrightBenchmark
from beta_team.sdk.analytics import MetricsCollector, ReportGenerator, DashboardVisualizer

# Example: Web application testing with Playwright
from beta_team.sdk.adapters import WebAdapter

adapter = WebAdapter()
adapter.configure({
    "browser": "chromium",
    "headless": True,
    "use_playwright": True,
})
adapter.connect("https://example.com")
result = adapter.run_test("visual_regression", visual_baseline="homepage")
adapter.disconnect()

# Example: Windows application benchmarking
from beta_team.sdk.benchmarks import WinAppDriverBenchmark

benchmark = WinAppDriverBenchmark()
benchmark.start_session("C:/path/to/app.exe")
benchmark.benchmark_element_find("xpath", "//Button[@Name='Submit']")
benchmark.benchmark_ui_response("btnTrigger", "lblResult")
metrics = benchmark.get_metrics()
benchmark.end_session()

# Example: Analytics and reporting
from beta_team.sdk.analytics import MetricsCollector, ReportGenerator

collector = MetricsCollector(storage_path="metrics.json")
collector.record_test_result("login_test", passed=True)
collector.record_response_time(150.5)
metrics = collector.get_real_time_metrics()

generator = ReportGenerator(output_dir="reports")
generator.add_issue("Login button unresponsive", "Button takes >5s to respond", severity="high")
generator.generate_html_report()
```

## Core Integration Options

### Video Games (Unity/Unreal)

```python
from beta_team.sdk.adapters import GameAdapter
from beta_team.sdk.benchmarks import AirTestBenchmark

# Game testing with BetaHub/AirTest integration
adapter = GameAdapter()
adapter.configure({
    "screenshot_dir": "screenshots",
    "airtest_enabled": True,
    "betahub_enabled": True,
})
adapter.connect("/path/to/game.exe")
result = adapter.run_test("gameplay_scenario", airtest_script="tests/tutorial.air")
metrics = adapter.collect_metrics()  # FPS, memory, etc.
adapter.disconnect()

# Cross-platform image-based automation
benchmark = AirTestBenchmark(platform="windows")
benchmark.connect("/path/to/game.exe")
benchmark.benchmark_image_match("templates/button.png")
benchmark.benchmark_fps(duration_seconds=30)
```

### VST Plugins/DAWs

```python
from beta_team.sdk.adapters import VSTAdapter

adapter = VSTAdapter()
adapter.configure({
    "daw_type": "reaper",
    "daw_path": "C:/Program Files/REAPER/reaper.exe",
})
adapter.connect("/path/to/plugin.vst3")
result = adapter.run_test("plugin_load")
result = adapter.run_test("preset_scan")
result = adapter.run_test("audio_render", audio_file="test.wav")
adapter.validate_clap_module("sapphire")  # CLAP format support
```

### Web Applications

```python
from beta_team.sdk.adapters import WebAdapter
from beta_team.sdk.benchmarks import PlaywrightBenchmark, SeleniumGridBenchmark

# Single browser testing with Playwright
adapter = WebAdapter()
adapter.configure({
    "browser": "chromium",
    "use_playwright": True,
    "baseline_dir": "baselines",
})
adapter.connect("https://app.example.com")
result = adapter.run_test("visual_regression", visual_baseline="dashboard")
result = adapter.run_test("element_check", selector="#login-btn", expected_text="Login")

# Parallel browser/OS testing with Selenium Grid
grid = SeleniumGridBenchmark(hub_url="http://localhost:4444/wd/hub")
results = grid.run_benchmark("https://app.example.com", configs=[
    {"browser": "chrome", "platform": "windows"},
    {"browser": "firefox", "platform": "linux"},
    {"browser": "edge", "platform": "windows"},
])
```

### Windows Applications

```python
from beta_team.sdk.adapters import WindowsAdapter
from beta_team.sdk.benchmarks import WinAppDriverBenchmark

adapter = WindowsAdapter()
adapter.configure({
    "winappdriver_url": "http://127.0.0.1:4723",
    "startup_timeout": 15,
})
adapter.connect("C:/path/to/app.exe")
result = adapter.run_test("load_time")
result = adapter.run_test("ui_stability", duration=60)
result = adapter.run_test("element_interaction", element_id="btnSubmit", action="click")
metrics = adapter.collect_metrics()  # Memory, CPU, crash count
```

## Benchmarking Tools

### WinAppDriver (Desktop)

```python
from beta_team.sdk.benchmarks import WinAppDriverBenchmark

benchmark = WinAppDriverBenchmark()
benchmark.start_session("C:/app.exe")
benchmark.benchmark_element_find("xpath", "//Button")
benchmark.benchmark_action_execution("submitBtn", "click")
benchmark.benchmark_ui_response("trigger", "response")
stability = benchmark.run_stability_benchmark(duration_seconds=120)
benchmark.end_session()
```

### AirTest (Games)

```python
from beta_team.sdk.benchmarks import AirTestBenchmark

benchmark = AirTestBenchmark(platform="android")
benchmark.connect("Android:///")
benchmark.benchmark_image_match("templates/enemy.png")
benchmark.benchmark_touch_response(500, 500)
fps_data = benchmark.benchmark_fps(duration_seconds=60)
benchmark.collect_android_metrics("com.game.package")
```

### Selenium Grid (Parallel Testing)

```python
from beta_team.sdk.benchmarks import SeleniumGridBenchmark

grid = SeleniumGridBenchmark()
status = grid.check_grid_status()
capabilities = grid.get_available_capabilities()

# Run parallel benchmarks
metrics = grid.run_benchmark("https://example.com")
print(f"Passed: {metrics.passed_tests}/{metrics.total_tests}")

# Compare browsers
comparison = grid.compare_browsers("https://example.com", ["chrome", "firefox", "edge"])
```

## Analytics and Visualization

### Metrics Collection (Statsig-like)

```python
from beta_team.sdk.analytics import MetricsCollector

collector = MetricsCollector(storage_path="metrics.json")

# Record metrics
collector.record_test_result("login_test", passed=True)
collector.record_test_result("login_test", passed=False)  # Flaky detection
collector.record_crash()
collector.record_response_time(150.5)

# Get real-time metrics
metrics = collector.get_real_time_metrics()
print(f"Pass rate: {metrics.pass_rate}%")
print(f"Crash rate: {metrics.crash_rate}/hour")
print(f"Flaky rate: {metrics.flaky_test_rate}%")

# Detect flaky tests
flaky = collector.get_flaky_tests(min_runs=3)
```

### Report Generation (Allure-compatible)

```python
from beta_team.sdk.analytics import ReportGenerator, AllureReportAdapter

# Standard reports
generator = ReportGenerator(output_dir="reports")
generator.add_issue("Performance regression", "Load time increased 50%", severity="high")
generator.generate_html_report("report.html")
generator.generate_json_report("report.json")
bullets = generator.generate_bullet_points()

# Allure format
allure = AllureReportAdapter(output_dir="allure-results")
allure.add_test_result(test_case, suite_name="regression")
allure.write_results()
allure.generate_environment({"Browser": "Chrome", "OS": "Windows"})
```

### Dashboard Visualization

```python
from beta_team.sdk.analytics import DashboardVisualizer

viz = DashboardVisualizer(output_dir="dashboard")

# Add charts
viz.add_pass_fail_chart("Test Results", passed=85, failed=10, skipped=5)
viz.add_trend_chart("Pass Rate Trend", ["Mon", "Tue", "Wed"], [90, 85, 92])

# Add screenshot diffs
viz.add_screenshot_diff("homepage", "baseline.png", "current.png", "diff.png")

# Generate heatmap
viz.add_heatmap_entry("login_test", "2024-01-01", "failed")
viz.add_heatmap_entry("login_test", "2024-01-02", "passed")
viz.generate_heatmap_chart()

# Export dashboard
viz.generate_html_dashboard("Beta Team Dashboard")
```

## Beta Team Launcher

A comprehensive beta testing dashboard with Robot Framework integration for automated testing scenarios.

### Requirements

- **OS**: Windows, macOS, Linux
- **Python**: >= 3.10

### Installation

```bash
# Install core packages
pip install robotframework robotframework-seleniumlibrary pillow selenium

# Install SDK dependencies (optional, based on your needs)
pip install playwright psutil  # For web testing
pip install airtest           # For game testing

# Download browser drivers as needed
# ChromeDriver: https://chromedriver.chromium.org/
# Playwright: npx playwright install
```

### Project Structure

```
beta_team/
├── launcher.py              # Main dashboard
├── sdk/                     # Modular SDK
│   ├── core/               # Base classes and registry
│   │   ├── base.py         # BaseAdapter, TestResult, BenchmarkMetrics
│   │   └── registry.py     # AdapterRegistry
│   ├── adapters/           # Software-specific adapters
│   │   ├── game_adapter.py     # Video games (Unity/Unreal)
│   │   ├── vst_adapter.py      # VST/DAW plugins
│   │   ├── web_adapter.py      # Web applications
│   │   └── windows_adapter.py  # Windows applications
│   ├── benchmarks/         # Benchmarking integrations
│   │   ├── winappdriver.py     # Windows desktop benchmarks
│   │   ├── airtest.py          # Game automation benchmarks
│   │   ├── playwright.py       # Web performance benchmarks
│   │   └── selenium_grid.py    # Parallel browser benchmarks
│   └── analytics/          # Metrics and visualization
│       ├── metrics.py          # Real-time metrics (Statsig-like)
│       ├── reports.py          # Report generation (Allure-compatible)
│       └── visualizer.py       # Dashboard visualization
├── tests/                   # Robot Framework test suites
│   ├── onboarding.robot
│   ├── poweruser.robot
│   └── edgecases.robot
├── builds/                  # Drop your EXEs here
├── reports/                 # Auto-generated HTML/JSON
├── results.json             # Benchmark history
└── beta.json                # Build manifest
```

### Setup Steps

1. Clone the repository
2. Navigate to `beta_team/` folder
3. Run `pip install robotframework robotframework-seleniumlibrary selenium pillow`
4. Download ChromeDriver matching your Chrome version
5. Drop your EXE in `builds/` folder
6. Run `python launcher.py`
7. Browse build → toggle scenarios → Run Beta Team

### Usage

| Action | Description |
|--------|-------------|
| Drop build | Put EXE in `builds/` or browse any path |
| Toggle scenarios | Check onboarding/poweruser/edgecases |
| Run | Click 🚀 Run Beta Team → watch live results |
| Benchmarks | Auto-compares timing vs previous build |
| Extend | Add more .robot files to `tests/`, they'll auto-appear |

### Customization

- Replace SeleniumLibrary with AppiumLibrary for native desktop apps
- Add Windows Agent Arena tasks via subprocess calls
- Extend benchmarks: add screenshots, memory usage, crash detection
- Add CI: `python launcher.py --headless --build v1.2.exe`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `robot` not found | Run `pip install robotframework` |
| ChromeDriver error | Match ChromeDriver version to your Chrome |
| No tests run | Check `tests/*.robot` files exist and are valid Robot syntax |
