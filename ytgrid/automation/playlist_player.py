import time
from ytgrid.automation.player import VideoPlayer
from ytgrid.automation.url_resolver import URLResolver
from ytgrid.utils.logger import log_info, log_error

class PlaylistPlayer:
    def __init__(self):
        pass

    def play_video(self, url: str, speed: float, loop_count: int):
        log_info(f"Starting playlist automation for: {url}")
        resolved_videos = URLResolver.resolve(url)

        if not resolved_videos:
            log_error("No videos resolved from playlist URL.")
            raise Exception("Failed to resolve any videos from the provided playlist URL.")

        log_info(f"Resolved {len(resolved_videos)} videos in the playlist.")

        # Sequentially play each video in the playlist `loop_count` times
        for loop in range(loop_count):
            log_info(f"Playlist Loop {loop + 1}/{loop_count}")
            for index, video in enumerate(resolved_videos):
                vid_url = video['url']
                log_info(f"Playing video {index + 1}/{len(resolved_videos)}: {vid_url}")
                player = VideoPlayer()
                try:
                    player.play_video(vid_url, speed, 1) # play individual 1 time
                except Exception as e:
                    log_error(f"Failed to play playlist entry {vid_url}: {e}")

        log_info(f"Finished playlist automation for: {url}")
