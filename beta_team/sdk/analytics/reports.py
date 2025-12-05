"""
Report Generation for Beta Testing.

Provides report generation with:
- Allure Report format support
- Pass/fail statistics
- Historical trend tracking
- Duplicate issue merging
- AI-powered feedback summaries
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class TestCase:
    """A single test case result."""
    name: str
    status: str  # passed, failed, skipped, broken
    duration_ms: float
    description: str = ""
    steps: list = field(default_factory=list)
    attachments: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "description": self.description,
            "steps": self.steps,
            "attachments": self.attachments,
            "labels": self.labels,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
        }


@dataclass
class TestSuite:
    """A collection of test cases."""
    name: str
    test_cases: list[TestCase] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_test(self, test: TestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test)

    def get_statistics(self) -> dict:
        """Get pass/fail statistics."""
        total = len(self.test_cases)
        passed = sum(1 for t in self.test_cases if t.status == "passed")
        failed = sum(1 for t in self.test_cases if t.status == "failed")
        skipped = sum(1 for t in self.test_cases if t.status == "skipped")
        broken = sum(1 for t in self.test_cases if t.status == "broken")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "broken": broken,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
        }


class ReportGenerator:
    """
    Generator for test reports.

    Creates reports with:
    - Pass/fail statistics
    - Historical trends
    - Screenshot diffs
    - Heatmaps of failures
    - Bullet-point summaries
    - Duplicate issue merging
    """

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory for generated reports.
        """
        self.output_dir = output_dir
        self._suites: list[TestSuite] = []
        self._history: list[dict] = []
        self._issues: list[dict] = []

        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def add_suite(self, suite: TestSuite) -> None:
        """Add a test suite to the report."""
        self._suites.append(suite)

    def add_issue(self, title: str, description: str, severity: str = "medium",
                  test_name: Optional[str] = None, screenshot: Optional[str] = None) -> str:
        """
        Add an issue to the report with automatic duplicate detection.

        Args:
            title: Issue title.
            description: Issue description.
            severity: Issue severity (low, medium, high, critical).
            test_name: Associated test name.
            screenshot: Path to screenshot.

        Returns:
            Issue ID (may be merged with existing).
        """
        # Check for duplicates using simple title matching
        for existing in self._issues:
            if self._is_duplicate(title, existing["title"]):
                existing["occurrences"] = existing.get("occurrences", 1) + 1
                if test_name:
                    existing.setdefault("tests", []).append(test_name)
                return existing["id"]

        issue_id = f"ISSUE-{len(self._issues) + 1}"
        self._issues.append({
            "id": issue_id,
            "title": title,
            "description": description,
            "severity": severity,
            "test_name": test_name,
            "tests": [test_name] if test_name else [],
            "screenshot": screenshot,
            "occurrences": 1,
            "created": datetime.now().isoformat(),
        })

        return issue_id

    def _is_duplicate(self, title1: str, title2: str) -> bool:
        """Check if two issue titles are duplicates."""
        # Simple similarity check - could be enhanced with AI
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        return t1 == t2 or t1 in t2 or t2 in t1

    def generate_summary(self) -> dict:
        """
        Generate a summary of all test results.

        Returns:
            Dictionary with summary data.
        """
        all_stats = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "broken": 0}

        for suite in self._suites:
            stats = suite.get_statistics()
            for key in all_stats:
                all_stats[key] += stats.get(key, 0)

        all_stats["pass_rate"] = (
            all_stats["passed"] / all_stats["total"] * 100
            if all_stats["total"] > 0 else 0
        )

        return {
            "statistics": all_stats,
            "issues": len(self._issues),
            "critical_issues": sum(1 for i in self._issues if i["severity"] == "critical"),
            "suites": len(self._suites),
        }

    def generate_bullet_points(self) -> list[str]:
        """
        Generate bullet-point summary of issues and feedback.

        Returns:
            List of bullet-point strings.
        """
        summary = self.generate_summary()
        bullets = []

        # Overall status
        stats = summary["statistics"]
        bullets.append(f"• Ran {stats['total']} tests with {stats['pass_rate']:.1f}% pass rate")

        if stats["failed"] > 0:
            bullets.append(f"• {stats['failed']} tests failed")

        if stats["broken"] > 0:
            bullets.append(f"• {stats['broken']} tests broken (infrastructure issues)")

        # Issues summary
        critical = summary["critical_issues"]
        if critical > 0:
            bullets.append(f"• ⚠️ {critical} critical issues found")

        for issue in sorted(self._issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]]):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[issue["severity"]]
            occurrences = issue.get("occurrences", 1)
            occ_text = f" ({occurrences}x)" if occurrences > 1 else ""
            bullets.append(f"  {severity_icon} {issue['title']}{occ_text}")

        return bullets

    def generate_html_report(self, filename: str = "report.html") -> str:
        """
        Generate an HTML report.

        Args:
            filename: Output filename.

        Returns:
            Path to generated report.
        """
        summary = self.generate_summary()
        bullets = self.generate_bullet_points()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Beta Team Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 8px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: white; padding: 15px; border-radius: 4px; text-align: center; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .issues {{ margin-top: 20px; }}
        .issue {{ padding: 10px; margin: 5px 0; border-left: 3px solid; }}
        .critical {{ border-color: red; background: #fff0f0; }}
        .high {{ border-color: orange; background: #fff8f0; }}
        .medium {{ border-color: yellow; background: #fffef0; }}
        .low {{ border-color: green; background: #f0fff0; }}
    </style>
</head>
<body>
    <h1>Beta Team Test Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>{summary['statistics']['total']}</h3>
                <p>Total Tests</p>
            </div>
            <div class="stat-box passed">
                <h3>{summary['statistics']['passed']}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h3>{summary['statistics']['failed']}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-box">
                <h3>{summary['statistics']['pass_rate']:.1f}%</h3>
                <p>Pass Rate</p>
            </div>
        </div>
    </div>

    <div class="issues">
        <h2>Issues ({len(self._issues)})</h2>
"""

        for issue in self._issues:
            html += f"""
        <div class="issue {issue['severity']}">
            <strong>{issue['title']}</strong>
            <p>{issue['description']}</p>
            <small>Occurrences: {issue.get('occurrences', 1)}</small>
        </div>
"""

        html += """
    </div>

    <div class="bullets">
        <h2>Key Points</h2>
        <ul>
"""
        for bullet in bullets:
            html += f"            <li>{bullet}</li>\n"

        html += """
        </ul>
    </div>
</body>
</html>
"""

        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w") as f:
            f.write(html)

        return output_path

    def generate_json_report(self, filename: str = "report.json") -> str:
        """
        Generate a JSON report.

        Args:
            filename: Output filename.

        Returns:
            Path to generated report.
        """
        report = {
            "generated": datetime.now().isoformat(),
            "summary": self.generate_summary(),
            "bullet_points": self.generate_bullet_points(),
            "issues": self._issues,
            "suites": [
                {
                    "name": suite.name,
                    "statistics": suite.get_statistics(),
                    "tests": [t.to_dict() for t in suite.test_cases],
                }
                for suite in self._suites
            ],
        }

        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return output_path

    def load_history(self, history_file: str) -> None:
        """Load historical report data for trend analysis."""
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                self._history = json.load(f)

    def get_trends(self) -> dict:
        """
        Get historical trends from loaded history.

        Returns:
            Dictionary with trend data.
        """
        if not self._history:
            return {}

        pass_rates = [h["summary"]["statistics"]["pass_rate"] for h in self._history if "summary" in h]
        return {
            "pass_rate_trend": pass_rates,
            "avg_pass_rate": sum(pass_rates) / len(pass_rates) if pass_rates else 0,
            "total_runs": len(self._history),
        }


class AllureReportAdapter:
    """
    Adapter for Allure Report format.

    Generates Allure-compatible reports for integration with
    Allure Report viewers and CI systems.
    """

    def __init__(self, output_dir: str = "allure-results"):
        """
        Initialize the Allure adapter.

        Args:
            output_dir: Directory for Allure results.
        """
        self.output_dir = output_dir
        self._containers: list[dict] = []
        self._results: list[dict] = []

        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def add_test_result(self, test_case: TestCase, suite_name: str = "default") -> None:
        """
        Add a test result in Allure format.

        Args:
            test_case: The test case to add.
            suite_name: Name of the test suite.
        """
        import uuid

        result = {
            "uuid": str(uuid.uuid4()),
            "historyId": test_case.name,
            "name": test_case.name,
            "status": test_case.status,
            "stage": "finished",
            "description": test_case.description,
            "steps": [
                {"name": step, "status": "passed"}
                for step in test_case.steps
            ],
            "attachments": [
                {"name": att, "source": att, "type": "image/png"}
                for att in test_case.attachments
            ],
            "labels": [
                {"name": "suite", "value": suite_name},
                {"name": "host", "value": "localhost"},
            ] + [
                {"name": k, "value": v} for k, v in test_case.labels.items()
            ],
            "start": int(time.time() * 1000),
            "stop": int(time.time() * 1000) + int(test_case.duration_ms),
        }

        if test_case.error_message:
            result["statusDetails"] = {
                "message": test_case.error_message,
                "trace": test_case.stack_trace or "",
            }

        self._results.append(result)

    def write_results(self) -> None:
        """Write all results to Allure format files."""
        for result in self._results:
            filename = f"{result['uuid']}-result.json"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "w") as f:
                json.dump(result, f, indent=2)

    def generate_environment(self, env_data: dict) -> None:
        """
        Generate environment.properties file.

        Args:
            env_data: Dictionary of environment properties.
        """
        filepath = os.path.join(self.output_dir, "environment.properties")
        with open(filepath, "w") as f:
            for key, value in env_data.items():
                f.write(f"{key}={value}\n")

    def generate_categories(self, categories: Optional[list[dict]] = None) -> None:
        """
        Generate categories.json for test categorization.

        Args:
            categories: List of category definitions.
        """
        if categories is None:
            categories = [
                {
                    "name": "Product defects",
                    "matchedStatuses": ["failed"],
                },
                {
                    "name": "Test defects",
                    "matchedStatuses": ["broken"],
                },
            ]

        filepath = os.path.join(self.output_dir, "categories.json")
        with open(filepath, "w") as f:
            json.dump(categories, f, indent=2)
