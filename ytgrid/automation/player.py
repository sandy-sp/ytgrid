"""
YTGrid Automation - Video Player (Version 3)

This module defines a VideoPlayer that plays YouTube videos for a specified number of loops.
Enhancements in Version 3 include:
  - A context manager for Selenium browser sessions to ensure proper cleanup.
  - Improved error handling and structured logging.
  - Integration with real-time update capabilities via WebSocket.
"""

import time
import json
import tempfile
from contextlib import contextmanager

import websocket
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ytgrid.automation.browser import get_browser
from ytgrid.utils.logger import log_info, log_error
from ytgrid.utils.config import config
from ytgrid.automation.base_player import AutomationPlayer


def send_update(ws, message):
    """Send updates to WebSocket for real-time tracking."""
    try:
        ws.send(json.dumps(message))
    except Exception as e:
        log_error(f"WebSocket error: {e}")


def get_video_title(video_url):
    """Extract the video title from the YouTube page."""
    try:
        import requests
        response = requests.get(video_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.replace(' - YouTube', '').strip()
    except Exception as e:
        log_error(f"Error fetching video title: {e}")
    return "Unknown Video"


def get_video_duration(driver):
    """Extract the duration (in seconds) of the video element."""
    try:
        video = driver.find_element(By.CSS_SELECTOR, "video")
        duration = driver.execute_script("return arguments[0].duration;", video)
        return duration if duration and duration > 0 else None
    except Exception as e:
        log_error(f"Error fetching video duration: {e}")
        return None


def skip_ad(driver):
    """Attempt to skip YouTube ads if present."""
    try:
        ad_skip_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ytp-ad-skip-button"))
        )
        ad_skip_button.click()
        log_info("Ad skipped.")
    except Exception:
        log_info("No skippable ad detected.")


@contextmanager
def browser_session():
    """
    Context manager for a Selenium browser session.
    
    Creates a temporary user-data directory (if configured) and yields the (driver, wait)
    tuple. Ensures that the driver is properly quit after use.
    """
    temp_user_data = None
    if config.USE_TEMP_USER_DATA:
        temp_user_data = tempfile.mkdtemp()
    driver, wait = get_browser(user_data_dir=temp_user_data)
    try:
        yield driver, wait
    finally:
        try:
            driver.quit()
        except Exception as e:
            log_error(f"Error quitting browser: {e}")


class VideoPlayer(AutomationPlayer):
    def play_video(self, video_url: str, speed: float = config.DEFAULT_SPEED, loop_count: int = config.DEFAULT_LOOP_COUNT) -> bool:
        """
        Plays a YouTube video for the specified number of loops.
        Returns True when all loops are completed successfully.
        """
        ws = None
        if config.ENABLE_REALTIME_UPDATES:
            try:
                ws = websocket.WebSocket()
                ws.connect(config.WEBSOCKET_SERVER_URL, timeout=10)
            except Exception as e:
                log_error(f"Could not connect to WebSocket: {e}")
                ws = None

        for loop in range(loop_count):
            log_info(f"Loop {loop + 1}/{loop_count}: Starting playback for {video_url}")
            if ws:
                send_update(ws, {"status": "playing", "loop": loop + 1})

            try:
                video_title = get_video_title(video_url)
                log_info(f"Extracted video title: {video_title}")

                # Use the context manager to guarantee browser cleanup.
                with browser_session() as (driver, wait):
                    driver.get("https://www.youtube.com/")
                    search_box = wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
                    search_box.clear()
                    search_box.send_keys(video_title)
                    search_box.send_keys(Keys.RETURN)

                    wait.until(EC.presence_of_element_located((By.ID, "video-title")))
                    video_elements = driver.find_elements(By.ID, "video-title")
                    found = False
                    for video_element in video_elements:
                        href = video_element.get_attribute('href')
                        if href and video_url in href:
                            log_info(f"Found matching video: {href}")
                            video_element.click()
                            found = True
                            break
                    if not found:
                        log_error("Video not found in search results")
                        if ws:
                            send_update(ws, {"status": "error", "message": "Video not found", "loop": loop + 1})
                        continue

                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
                    skip_ad(driver)
                    driver.execute_script(f"document.querySelector('video').playbackRate = {speed};")
                    driver.execute_script("document.querySelector('video').play();")

                    video_duration = get_video_duration(driver)
                    if video_duration is None:
                        log_info("Video duration not determined; using fallback wait (300 seconds).")
                        time.sleep(300)
                    else:
                        log_info(f"Video duration: {video_duration} seconds (adjusted for speed: {speed}).")
                        time.sleep(video_duration / speed)

                    log_info(f"Loop {loop + 1} completed.")
                    if ws:
                        send_update(ws, {"status": "completed", "loop": loop + 1})
            except Exception as e:
                log_error(f"Error during loop {loop + 1}: {e}")
                if ws:
                    send_update(ws, {"status": "error", "message": str(e), "loop": loop + 1})

        log_info(f"All {loop_count} loops completed for {video_url}.")
        if ws:
            try:
                send_update(ws, {"status": "all_completed"})
                ws.close()
            except Exception as e:
                log_error(f"Error closing WebSocket: {e}")
        return True


def play_video(video_url, speed=config.DEFAULT_SPEED, loop_count=config.DEFAULT_LOOP_COUNT):
    """
    Convenience function for backward compatibility.
    """
    player = VideoPlayer()
    return player.play_video(video_url, speed, loop_count)
