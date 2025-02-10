import tempfile
import uuid
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from ytgrid.utils.config import config

# Define maximum number of retries and delay between retries
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds

def get_browser(user_data_dir=None):
    """Initialize and return a Chrome browser instance with a unique, temporary profile.
    
    This function uses incognito mode and creates a unique user-data-dir for each session.
    If the browser fails to launch due to a locked or in-use profile, it will retry up to MAX_RETRIES times.
    """
    options = Options()

    # Enable headless mode if configured.
    if config.HEADLESS_MODE:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Use incognito mode
    options.add_argument("--incognito")
    # Generate a unique temporary user-data directory
    user_data_dir = tempfile.mkdtemp(prefix=str(uuid.uuid4()) + "_")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    # Initialize ChromeDriver service
    service = Service(ChromeDriverManager().install())

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
            return driver, wait
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt} failed to create Chrome session: {e}")
            time.sleep(RETRY_DELAY)
    raise Exception("Failed to create a Chrome session after multiple retries")
