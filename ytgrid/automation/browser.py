import tempfile
import uuid
import time
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from ytgrid.utils.config import config
from ytgrid.utils.logger import log_info, log_error

# Define maximum number of retries and delay between retries
MAX_RETRIES: int = 3
RETRY_DELAY: int = 3  # seconds

def get_browser(user_data_dir: Optional[str] = None) -> Tuple[webdriver.Chrome, WebDriverWait]:
    """
    Initialize and return a Chrome browser instance with a unique, temporary profile.

    This function uses incognito mode and creates a unique user-data directory for each session.
    If the browser fails to launch due to a locked or in-use profile, it will retry up to MAX_RETRIES times.

    :param user_data_dir: Optional path to an existing user-data directory. If not provided, a temporary directory is created.
    :return: A tuple containing the Chrome WebDriver instance and a WebDriverWait instance.
    :raises Exception: If a Chrome session cannot be created after multiple retries.
    """
    options = Options()

    # Enable headless mode if configured.
    if config.HEADLESS_MODE:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")

    # Use provided user_data_dir or create a new temporary directory
    if user_data_dir is None:
        user_data_dir = tempfile.mkdtemp(prefix=f"{uuid.uuid4()}_")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    # Initialize ChromeDriver service using webdriver-manager
    service = Service(ChromeDriverManager().install())

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
            log_info(f"Chrome session created successfully on attempt {attempt + 1}.")
            return driver, wait
        except Exception as e:
            attempt += 1
            log_error(f"Attempt {attempt} failed to create Chrome session: {e}")
            time.sleep(RETRY_DELAY)

    log_error("Failed to create a Chrome session after multiple retries.")
    raise Exception("Failed to create a Chrome session after multiple retries")
