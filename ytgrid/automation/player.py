import time
import requests
import json
import tempfile
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import websocket

from ytgrid.automation.browser import get_browser
from ytgrid.utils.logger import log_info, log_error
from ytgrid.utils.config import config


def send_update(ws, message):
    """Send updates to WebSocket for real-time tracking."""
    try:
        ws.send(json.dumps(message))
    except Exception as e:
        log_error(f"WebSocket error: {e}")


def get_video_title(video_url):
    """Extracts the video title from the YouTube page."""
    response = requests.get(video_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    return title.text.replace(' - YouTube', '') if title else "Unknown Video"


def get_video_duration(driver, wait):
    """Extracts the duration of the video in seconds."""
    try:
        video = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
        duration = driver.execute_script("return arguments[0].duration;", video)
        return duration if duration and duration > 0 else None
    except Exception as e:
        log_error(f"Error fetching video duration: {e}")
        return None


def play_video(video_url, speed=config.DEFAULT_SPEED, loop_count=config.DEFAULT_LOOP_COUNT):
    """Plays a YouTube video for `loop_count` times, restarting the entire process each time."""
    
    ws = None
    if config.ENABLE_REALTIME_UPDATES:
        try:
            ws = websocket.WebSocket()
            ws.connect(config.WEBSOCKET_SERVER_URL)
        except Exception as e:
            log_error(f"Could not connect to WebSocket: {e}")

    for loop in range(loop_count):
        temp_user_data = None
        if config.USE_TEMP_USER_DATA:
            temp_user_data = tempfile.mkdtemp()

        driver, wait = get_browser(user_data_dir=temp_user_data)

        try:
            log_info(f"Loop {loop + 1}/{loop_count}: Playing {video_url}")
            send_update(ws, {"status": "playing", "loop": loop + 1, "total_loops": loop_count})

            video_title = get_video_title(video_url)

            # Open YouTube and search for the video title
            driver.get("https://www.youtube.com/")
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
            search_box.send_keys(video_title)
            search_box.send_keys(Keys.RETURN)

            # Wait for search results and click the first matching video
            wait.until(EC.presence_of_element_located((By.ID, "video-title")))
            video_elements = driver.find_elements(By.ID, "video-title")
            for video_element in video_elements:
                href = video_element.get_attribute('href')
                if href and video_url in href:
                    video_element.click()
                    break
            else:
                log_error("Video not found in search results")
                send_update(ws, {"status": "error", "message": "Video not found in search results"})
                continue  # Skip this loop iteration

            # Wait for the video to load
            video = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))

            # Set playback speed
            driver.execute_script(f"arguments[0].playbackRate = {speed};", video)

            # Get video duration
            video_duration = get_video_duration(driver, wait)
            if video_duration is None:
                log_info("Could not determine video duration, waiting manually for 5 minutes.")
                time.sleep(300)  # Fallback wait time
            else:
                log_info(f"Video Duration: {video_duration} seconds")
                time.sleep(video_duration / speed)

            log_info(f"Loop {loop + 1}/{loop_count} completed.")
            send_update(ws, {"status": "completed", "loop": loop + 1, "total_loops": loop_count})

        except Exception as e:
            log_error(f"Error: {e}")
            send_update(ws, {"status": "error", "message": str(e)})

        finally:
            driver.quit()

    log_info(f"All {loop_count} loops completed for {video_url}.")
    send_update(ws, {"status": "all_completed", "total_loops": loop_count})

    if ws:
        ws.close()
