"""Adapters for different software types."""

from beta_team.sdk.adapters.game_adapter import GameAdapter
from beta_team.sdk.adapters.vst_adapter import VSTAdapter
from beta_team.sdk.adapters.web_adapter import WebAdapter
from beta_team.sdk.adapters.windows_adapter import WindowsAdapter

__all__ = [
    "GameAdapter",
    "VSTAdapter",
    "WebAdapter",
    "WindowsAdapter",
]
