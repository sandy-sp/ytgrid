import tempfile
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from ytgrid.utils.config import config

def get_browser(user_data_dir=None):
    """Initialize and return a Chrome browser instance with a fresh, isolated session."""
    
    options = Options()

    # Enable headless mode if configured.
    if config.HEADLESS_MODE:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Instead of using a user-data-dir, we use incognito mode to create an isolated session.
    if config.USE_TEMP_USER_DATA:
        options.add_argument("--incognito")
        # If you still want to use a unique user-data-dir, you can uncomment the following:
        # unique_dir = tempfile.mkdtemp(prefix=str(uuid.uuid4()) + "_")
        # options.add_argument(f"--user-data-dir={unique_dir}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
    return driver, wait
