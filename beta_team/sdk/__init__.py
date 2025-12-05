"""
Beta Team SDK - Modular architecture for deep integration into diverse software.

This SDK provides adapters and APIs for integration with:
- Video Games (Unity, Unreal with BetaHub/AirTest)
- VST Plugins and DAWs (VST3/AU/CLAP)
- Web Applications (Playwright/Selenium)
- Windows Applications (WinAppDriver/Winium)
"""

from beta_team.sdk.core.base import BaseAdapter, TestResult, BenchmarkMetrics
from beta_team.sdk.core.registry import AdapterRegistry

__version__ = "1.0.0"
__all__ = [
    "BaseAdapter",
    "TestResult",
    "BenchmarkMetrics",
    "AdapterRegistry",
]
