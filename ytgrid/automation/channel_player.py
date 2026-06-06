from ytgrid.automation.playlist_player import PlaylistPlayer
from ytgrid.utils.logger import log_info

class ChannelPlayer(PlaylistPlayer):
    def __init__(self):
        super().__init__()

    def play_video(self, url: str, speed: float, loop_count: int):
        log_info(f"Starting channel automation for: {url}")
        super().play_video(url, speed, loop_count)
