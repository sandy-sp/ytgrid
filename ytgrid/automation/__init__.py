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
from .playlist_player import PlaylistPlayer
from .channel_player import ChannelPlayer
from .browser import get_browser

# Map task_type string to the class responsible for it
AUTOMATION_PLAYERS = {
    "video": VideoPlayer,
    "playlist": PlaylistPlayer,
    "channel": ChannelPlayer
}
