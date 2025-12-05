"""Benchmarking integrations for various automation tools."""

from beta_team.sdk.benchmarks.winappdriver import WinAppDriverBenchmark
from beta_team.sdk.benchmarks.airtest import AirTestBenchmark
from beta_team.sdk.benchmarks.playwright import PlaywrightBenchmark
from beta_team.sdk.benchmarks.selenium_grid import SeleniumGridBenchmark

__all__ = [
    "WinAppDriverBenchmark",
    "AirTestBenchmark",
    "PlaywrightBenchmark",
    "SeleniumGridBenchmark",
]
