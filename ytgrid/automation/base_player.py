# ytgrid/automation/base_player.py

from abc import ABC, abstractmethod

class AutomationPlayer(ABC):
    @abstractmethod
    def play_video(self, video_url: str, speed: float, loop_count: int) -> bool:
        """
        Plays a video given its URL, playback speed, and loop count.
        Must return True if the operation succeeds.
        """
        pass
