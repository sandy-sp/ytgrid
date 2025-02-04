import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from ytgrid.utils.config import config

def get_browser(user_data_dir=None):
    """Initialize and return a Chrome browser instance with optional fresh session data."""
    
    options = Options()

    # Set headless mode based on config
    if config.HEADLESS_MODE:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Use a fresh browser session if enabled
    if config.USE_TEMP_USER_DATA:
        user_data_dir = user_data_dir or tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={user_data_dir}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 20)

    return driver, wait
