"""
Dashboard Visualizer for Beta Testing.

Provides visualization components for:
- Interactive charts
- Screenshot diffs
- Heatmaps
- Pass/fail statistics
- Historical trends
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class ChartData:
    """Data for a chart visualization."""
    title: str
    chart_type: str  # line, bar, pie, heatmap
    labels: list[str] = field(default_factory=list)
    datasets: list[dict] = field(default_factory=list)
    options: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "type": self.chart_type,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options,
        }


class DashboardVisualizer:
    """
    Visualizer for creating analytics dashboards.

    Supports:
    - VisualRegressionTracker integration patterns
    - Allure Report style visualizations
    - Interactive charts
    - Screenshot diff views
    - Heatmaps for failure patterns
    """

    def __init__(self, output_dir: str = "dashboard"):
        """
        Initialize the visualizer.

        Args:
            output_dir: Directory for dashboard output.
        """
        self.output_dir = output_dir
        self._charts: list[ChartData] = []
        self._screenshots: list[dict] = []
        self._heatmap_data: list[dict] = []

        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def add_pass_fail_chart(self, title: str, passed: int, failed: int, skipped: int = 0) -> ChartData:
        """
        Add a pass/fail pie chart.

        Args:
            title: Chart title.
            passed: Number of passed tests.
            failed: Number of failed tests.
            skipped: Number of skipped tests.

        Returns:
            ChartData object.
        """
        chart = ChartData(
            title=title,
            chart_type="pie",
            labels=["Passed", "Failed", "Skipped"],
            datasets=[{
                "data": [passed, failed, skipped],
                "backgroundColor": ["#4CAF50", "#f44336", "#9E9E9E"],
            }],
        )
        self._charts.append(chart)
        return chart

    def add_trend_chart(self, title: str, labels: list[str], data_points: list[float],
                       dataset_label: str = "Pass Rate") -> ChartData:
        """
        Add a line chart for trends.

        Args:
            title: Chart title.
            labels: X-axis labels (e.g., dates).
            data_points: Y-axis values.
            dataset_label: Label for the data series.

        Returns:
            ChartData object.
        """
        chart = ChartData(
            title=title,
            chart_type="line",
            labels=labels,
            datasets=[{
                "label": dataset_label,
                "data": data_points,
                "borderColor": "#2196F3",
                "fill": False,
            }],
            options={"responsive": True},
        )
        self._charts.append(chart)
        return chart

    def add_bar_chart(self, title: str, labels: list[str], datasets: list[dict]) -> ChartData:
        """
        Add a bar chart for comparisons.

        Args:
            title: Chart title.
            labels: X-axis labels.
            datasets: List of dataset configs with label, data, and color.

        Returns:
            ChartData object.
        """
        chart = ChartData(
            title=title,
            chart_type="bar",
            labels=labels,
            datasets=datasets,
        )
        self._charts.append(chart)
        return chart

    def add_screenshot_diff(self, name: str, baseline_path: str, current_path: str,
                           diff_path: Optional[str] = None) -> dict:
        """
        Add a screenshot diff comparison.

        Args:
            name: Name of the comparison.
            baseline_path: Path to baseline screenshot.
            current_path: Path to current screenshot.
            diff_path: Optional path to diff image.

        Returns:
            Screenshot diff data.
        """
        diff_data = {
            "name": name,
            "baseline": baseline_path,
            "current": current_path,
            "diff": diff_path,
            "timestamp": datetime.now().isoformat(),
        }
        self._screenshots.append(diff_data)
        return diff_data

    def add_heatmap_entry(self, test_name: str, date: str, status: str) -> None:
        """
        Add an entry for the failure heatmap.

        Args:
            test_name: Name of the test.
            date: Date string.
            status: Test status (passed, failed, etc.).
        """
        self._heatmap_data.append({
            "test": test_name,
            "date": date,
            "status": status,
            "value": 1 if status == "failed" else 0,
        })

    def generate_heatmap_chart(self, title: str = "Failure Heatmap") -> ChartData:
        """
        Generate a heatmap from collected data.

        Args:
            title: Chart title.

        Returns:
            ChartData for the heatmap.
        """
        # Group by test and date
        tests = sorted(set(d["test"] for d in self._heatmap_data))
        dates = sorted(set(d["date"] for d in self._heatmap_data))

        matrix = []
        for test in tests:
            row = []
            for date in dates:
                entry = next(
                    (d for d in self._heatmap_data if d["test"] == test and d["date"] == date),
                    None
                )
                row.append(entry["value"] if entry else 0)
            matrix.append(row)

        chart = ChartData(
            title=title,
            chart_type="heatmap",
            labels=dates,
            datasets=[{
                "labels": tests,
                "data": matrix,
            }],
        )
        self._charts.append(chart)
        return chart

    def generate_html_dashboard(self, title: str = "Beta Team Dashboard") -> str:
        """
        Generate an HTML dashboard with all visualizations.

        Args:
            title: Dashboard title.

        Returns:
            Path to generated HTML file.
        """
        charts_json = json.dumps([c.to_dict() for c in self._charts])
        screenshots_json = json.dumps(self._screenshots)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 10px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .screenshot-diff {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .diff-images {{
            display: flex;
            gap: 20px;
            justify-content: space-around;
        }}
        .diff-images img {{
            max-width: 30%;
            border: 1px solid #ddd;
        }}
        .diff-label {{
            text-align: center;
            margin-top: 5px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>{title}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="charts-grid" id="charts-container">
        </div>

        <div id="screenshots-container">
        </div>
    </div>

    <script>
        const chartsData = {charts_json};
        const screenshotsData = {screenshots_json};

        // Render charts
        const chartsContainer = document.getElementById('charts-container');
        chartsData.forEach((chartData, index) => {{
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-container';
            wrapper.innerHTML = '<h3>' + chartData.title + '</h3><canvas id="chart-' + index + '"></canvas>';
            chartsContainer.appendChild(wrapper);

            const ctx = document.getElementById('chart-' + index).getContext('2d');
            new Chart(ctx, {{
                type: chartData.type === 'heatmap' ? 'bar' : chartData.type,
                data: {{
                    labels: chartData.labels,
                    datasets: chartData.datasets.map(ds => ({{
                        label: ds.label || '',
                        data: ds.data,
                        backgroundColor: ds.backgroundColor || '#2196F3',
                        borderColor: ds.borderColor || '#2196F3',
                        fill: ds.fill !== undefined ? ds.fill : false,
                    }})),
                }},
                options: chartData.options || {{}},
            }});
        }});

        // Render screenshot diffs
        const screenshotsContainer = document.getElementById('screenshots-container');
        screenshotsData.forEach(diff => {{
            const wrapper = document.createElement('div');
            wrapper.className = 'screenshot-diff';
            wrapper.innerHTML = `
                <h3>Screenshot Diff: ${{diff.name}}</h3>
                <div class="diff-images">
                    <div>
                        <img src="${{diff.baseline}}" alt="Baseline" onerror="this.alt='Baseline not found'">
                        <div class="diff-label">Baseline</div>
                    </div>
                    <div>
                        <img src="${{diff.current}}" alt="Current" onerror="this.alt='Current not found'">
                        <div class="diff-label">Current</div>
                    </div>
                    ${{diff.diff ? `<div>
                        <img src="${{diff.diff}}" alt="Diff" onerror="this.alt='Diff not found'">
                        <div class="diff-label">Difference</div>
                    </div>` : ''}}
                </div>
            `;
            screenshotsContainer.appendChild(wrapper);
        }});
    </script>
</body>
</html>
"""

        output_path = os.path.join(self.output_dir, "dashboard.html")
        with open(output_path, "w") as f:
            f.write(html)

        return output_path

    def export_data(self, filename: str = "dashboard_data.json") -> str:
        """
        Export dashboard data as JSON.

        Args:
            filename: Output filename.

        Returns:
            Path to exported file.
        """
        data = {
            "generated": datetime.now().isoformat(),
            "charts": [c.to_dict() for c in self._charts],
            "screenshots": self._screenshots,
            "heatmap_data": self._heatmap_data,
        }

        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def clear(self) -> None:
        """Clear all visualizer data."""
        self._charts.clear()
        self._screenshots.clear()
        self._heatmap_data.clear()
