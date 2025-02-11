"""
YTGrid Automation Package

Exports:
    - AutomationPlayer: Abstract base class for automation players.
    - VideoPlayer: Concrete implementation for video automation.
    - play_video: Convenience function for backward compatibility.
    - get_browser: Utility function to obtain a Selenium Chrome WebDriver.
"""

__all__ = [
    "AutomationPlayer",
    "VideoPlayer",
    "play_video",
    "get_browser",
]

from .base_player import AutomationPlayer
from .player import VideoPlayer, play_video
from .browser import get_browser
