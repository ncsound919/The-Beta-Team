"""Unit tests for Beta Team SDK analytics components."""

import json
import os
import tempfile

from beta_team.sdk.analytics.metrics import MetricsCollector
from beta_team.sdk.analytics.reports import ReportGenerator, TestCase, TestSuite, AllureReportAdapter
from beta_team.sdk.analytics.visualizer import DashboardVisualizer


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_record_test_result(self):
        """Test recording test results."""
        collector = MetricsCollector()
        collector.record_test_result("test_login", passed=True)
        collector.record_test_result("test_login", passed=False)
        
        metrics = collector.get_real_time_metrics()
        assert metrics.total_tests == 2
        assert metrics.passed_tests == 1
        assert metrics.failed_tests == 1

    def test_pass_rate_calculation(self):
        """Test pass rate calculation."""
        collector = MetricsCollector()
        for _ in range(8):
            collector.record_test_result("test", passed=True)
        for _ in range(2):
            collector.record_test_result("test", passed=False)
        
        metrics = collector.get_real_time_metrics()
        assert metrics.pass_rate == 80.0

    def test_flaky_test_detection(self):
        """Test flaky test detection."""
        collector = MetricsCollector()
        # Flaky test with mixed results
        collector.record_test_result("flaky_test", passed=True)
        collector.record_test_result("flaky_test", passed=False)
        collector.record_test_result("flaky_test", passed=True)
        
        flaky = collector.get_flaky_tests(min_runs=3)
        assert len(flaky) == 1
        assert flaky[0]["name"] == "flaky_test"

    def test_record_crash(self):
        """Test recording crash events."""
        collector = MetricsCollector()
        collector.record_crash()
        collector.record_crash()
        
        # Crash rate is per hour, so just verify crashes are recorded
        assert len(collector._crash_events) == 2

    def test_response_time_recording(self):
        """Test recording response times."""
        collector = MetricsCollector()
        collector.record_response_time(100.0)
        collector.record_response_time(200.0)
        
        metrics = collector.get_real_time_metrics()
        assert metrics.avg_response_time_ms == 150.0

    def test_persistence(self):
        """Test saving and loading metrics."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            storage_path = f.name
        
        try:
            # Save metrics
            collector = MetricsCollector(storage_path=storage_path)
            collector.record_test_result("test1", passed=True)
            collector.record_response_time(100.0)
            collector.save()
            
            # Load metrics in new collector
            collector2 = MetricsCollector(storage_path=storage_path)
            assert collector2._response_times == [100.0]
        finally:
            os.unlink(storage_path)

    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        collector.record_test_result("test", passed=True)
        collector.record_crash()
        collector.reset()
        
        metrics = collector.get_real_time_metrics()
        assert metrics.total_tests == 0


class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_add_suite(self):
        """Test adding test suites."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            suite = TestSuite(name="regression")
            suite.add_test(TestCase(name="test1", status="passed", duration_ms=100))
            generator.add_suite(suite)
            
            assert len(generator._suites) == 1

    def test_add_issue_with_duplicate_detection(self):
        """Test adding issues with duplicate detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            id1 = generator.add_issue("Login failed", "Error message")
            id2 = generator.add_issue("Login failed", "Same error")  # Duplicate
            
            assert id1 == id2
            assert len(generator._issues) == 1
            assert generator._issues[0]["occurrences"] == 2

    def test_generate_summary(self):
        """Test generating summary statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            suite = TestSuite(name="test")
            suite.add_test(TestCase(name="t1", status="passed", duration_ms=100))
            suite.add_test(TestCase(name="t2", status="failed", duration_ms=200))
            generator.add_suite(suite)
            
            summary = generator.generate_summary()
            assert summary["statistics"]["total"] == 2
            assert summary["statistics"]["passed"] == 1
            assert summary["statistics"]["failed"] == 1

    def test_generate_bullet_points(self):
        """Test generating bullet point summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            generator.add_issue("Critical bug", "Description", severity="critical")
            
            bullets = generator.generate_bullet_points()
            assert len(bullets) > 0
            assert any("critical" in b.lower() for b in bullets)

    def test_generate_html_report(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            suite = TestSuite(name="test")
            suite.add_test(TestCase(name="t1", status="passed", duration_ms=100))
            generator.add_suite(suite)
            
            path = generator.generate_html_report()
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
                assert "Beta Team" in content

    def test_generate_json_report(self):
        """Test JSON report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator(output_dir=tmpdir)
            path = generator.generate_json_report()
            
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
                assert "summary" in data


class TestDashboardVisualizer:
    """Tests for DashboardVisualizer."""

    def test_add_pass_fail_chart(self):
        """Test adding pass/fail pie chart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = DashboardVisualizer(output_dir=tmpdir)
            chart = viz.add_pass_fail_chart("Tests", passed=10, failed=2, skipped=1)
            
            assert chart.title == "Tests"
            assert chart.chart_type == "pie"
            assert chart.datasets[0]["data"] == [10, 2, 1]

    def test_add_trend_chart(self):
        """Test adding trend line chart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = DashboardVisualizer(output_dir=tmpdir)
            chart = viz.add_trend_chart(
                "Pass Rate",
                labels=["Day 1", "Day 2", "Day 3"],
                data_points=[90, 85, 95],
            )
            
            assert chart.chart_type == "line"
            assert len(chart.labels) == 3

    def test_add_screenshot_diff(self):
        """Test adding screenshot diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = DashboardVisualizer(output_dir=tmpdir)
            diff = viz.add_screenshot_diff("homepage", "base.png", "current.png")
            
            assert diff["name"] == "homepage"
            assert len(viz._screenshots) == 1

    def test_generate_html_dashboard(self):
        """Test HTML dashboard generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = DashboardVisualizer(output_dir=tmpdir)
            viz.add_pass_fail_chart("Tests", passed=5, failed=1)
            
            path = viz.generate_html_dashboard()
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
                assert "chart.js" in content.lower()

    def test_export_data(self):
        """Test exporting dashboard data as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = DashboardVisualizer(output_dir=tmpdir)
            viz.add_pass_fail_chart("Tests", passed=5, failed=1)
            
            path = viz.export_data()
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
                assert "charts" in data


class TestAllureReportAdapter:
    """Tests for AllureReportAdapter."""

    def test_add_test_result(self):
        """Test adding test results in Allure format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allure = AllureReportAdapter(output_dir=tmpdir)
            test_case = TestCase(name="test1", status="passed", duration_ms=100)
            allure.add_test_result(test_case)
            
            assert len(allure._results) == 1
            assert allure._results[0]["status"] == "passed"

    def test_write_results(self):
        """Test writing Allure results to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allure = AllureReportAdapter(output_dir=tmpdir)
            test_case = TestCase(name="test1", status="passed", duration_ms=100)
            allure.add_test_result(test_case)
            allure.write_results()
            
            files = os.listdir(tmpdir)
            assert any(f.endswith("-result.json") for f in files)

    def test_generate_environment(self):
        """Test generating environment properties."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allure = AllureReportAdapter(output_dir=tmpdir)
            allure.generate_environment({"Browser": "Chrome", "OS": "Windows"})
            
            env_file = os.path.join(tmpdir, "environment.properties")
            assert os.path.exists(env_file)
