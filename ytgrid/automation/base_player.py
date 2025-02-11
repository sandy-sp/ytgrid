"""
YTGrid Automation - Base Player

This module defines the abstract base class for automation players.
Any concrete implementation (e.g. VideoPlayer) must implement the play_video method.
"""

from abc import ABC, abstractmethod

class AutomationPlayer(ABC):
    @abstractmethod
    def play_video(self, video_url: str, speed: float, loop_count: int) -> bool:
        """
        Plays a video given its URL, playback speed, and loop count.
        
        :param video_url: The URL of the video to be played.
        :param speed: The playback speed multiplier.
        :param loop_count: Number of times to play the video.
        :return: True if the operation succeeds, otherwise False.
        """
        pass
