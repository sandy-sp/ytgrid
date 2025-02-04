import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_video_title(video_url):
    """Extracts the video title from the YouTube page."""
    response = requests.get(video_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find('title').text.replace(' - YouTube', '')

def setup_driver():
    """Configures and returns a Selenium WebDriver with headless mode."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    return driver, wait

def get_video_duration(driver, wait):
    """Extracts the duration of the video in seconds, ensuring it is fully loaded first."""
    try:
        # Wait until the video player is fully ready
        video = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))

        # Ensure the video is interactable before extracting duration
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "video")))

        # Extract the duration
        duration = driver.execute_script("return arguments[0].duration;", video)

        if duration is None or duration <= 0:
            raise ValueError("Invalid or missing video duration")

        return duration

    except Exception as e:
        print(f"Error fetching video duration: {e}")
        return None  # Return None to handle gracefully

def play_video(video_url, speed=1.0):
    """Searches for the video on YouTube, plays it at specified speed, and waits for it to finish."""
    driver, wait = setup_driver()

    try:
        video_title = get_video_title(video_url)

        # Open YouTube and search for the video title
        driver.get("https://www.youtube.com/")
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
        search_box.send_keys(video_title)
        search_box.send_keys(Keys.RETURN)

        # Wait for search results and click the first relevant video
        wait.until(EC.presence_of_element_located((By.ID, "video-title")))
        video_elements = driver.find_elements(By.ID, "video-title")
        video_elements[0].click()

        print(f"Playing: {video_title}")

        # Wait for the video to load
        video = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))

        # Set playback speed
        driver.execute_script(f"arguments[0].playbackRate = {speed};", video)

        # Get video duration
        video_duration = get_video_duration(driver, wait)
        if video_duration is None:
            print("Could not determine video duration, waiting manually for 5 minutes.")
            time.sleep(300)  # Fallback: Wait 5 minutes before closing

        else:
            print(f"Video Duration: {video_duration} seconds")
            time.sleep(video_duration / speed)

        print("Video completed successfully.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()

# Test the function
if __name__ == "__main__":
    play_video("https://www.youtube.com/watch?v=OaOK76hiW8I", speed=1.0)
