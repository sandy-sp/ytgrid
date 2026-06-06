import os
import shutil
import tempfile
import uuid
import time
import zipfile
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from ytgrid.utils.config import config
from ytgrid.utils.logger import log_info, log_error
from ytgrid.backend.process_registry import process_registry
from ytgrid.proxy.models import Proxy

# Define maximum number of retries and delay between retries

MAX_RETRIES: int = 3
RETRY_DELAY: int = 3  # seconds

def _inject_proxy_auth_extension(options: Options, proxy: Proxy) -> str:
    """Build a throwaway Chrome extension that supplies proxy auth credentials.

    Returns the plugin directory so the caller can delete it once Chrome has
    loaded the extension (otherwise it leaks into /tmp on every launch).
    """
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = f"""
    var config = {{
            mode: "fixed_servers",
            rules: {{
              singleProxy: {{
                scheme: "{proxy.protocol.value}",
                host: "{proxy.host}",
                port: parseInt("{proxy.port}")
              }},
              bypassList: ["localhost"]
            }}
          }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{proxy.username}",
                password: "{proxy.password}"
            }}
        }};
    }}
    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {{urls: ["<all_urls>"]}},
                ['blocking']
    );
    """

    plugin_dir = tempfile.mkdtemp(prefix="ytgrid_proxy_", dir="/tmp")
    plugin_file = os.path.join(plugin_dir, "proxy_auth_plugin.zip")
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    options.add_extension(plugin_file)
    return plugin_dir

def get_browser(user_data_dir: Optional[str] = None, proxy: Optional[Proxy] = None) -> Tuple[webdriver.Chrome, WebDriverWait]:
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

    # SECURITY: Hardened Chrome flags
    security_flags = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--incognito",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-translate",
        "--disable-default-apps",
        "--disable-plugins",
        "--disable-infobars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-client-side-phishing-detection",
        "--disable-component-update",
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    proxy_plugin_dir = None
    if proxy:
        if proxy.username:
            # An authenticated proxy needs a Chrome extension. Extensions do
            # not load under --incognito, so both extension-blocking flags
            # must be dropped for this case.
            for incompatible in ("--disable-extensions", "--incognito"):
                if incompatible in security_flags:
                    security_flags.remove(incompatible)
            proxy_plugin_dir = _inject_proxy_auth_extension(options, proxy)
        else:
            options.add_argument(f"--proxy-server={proxy.extension_url}")

    for flag in security_flags:
        options.add_argument(flag)

    # SECURITY: Use isolated temp dir with restricted permissions
    if user_data_dir is None:
        user_data_dir = tempfile.mkdtemp(prefix="ytgrid_", dir="/tmp")
        os.chmod(user_data_dir, 0o700)
    options.add_argument(f"--user-data-dir={user_data_dir}")

    # Initialize ChromeDriver service using webdriver-manager
    service = Service(ChromeDriverManager().install())

    try:
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                driver = webdriver.Chrome(service=service, options=options)
                process_registry.register(driver.service.process.pid)
                wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
                log_info(f"Chrome session created successfully on attempt {attempt + 1}.")
                return driver, wait
            except Exception as e:
                attempt += 1
                log_error(f"Attempt {attempt} failed to create Chrome session: {e}")
                time.sleep(RETRY_DELAY)

        log_error("Failed to create a Chrome session after multiple retries.")
        raise Exception("Failed to create a Chrome session after multiple retries")
    finally:
        # Chrome has already read the extension by now — drop the temp copy.
        if proxy_plugin_dir:
            shutil.rmtree(proxy_plugin_dir, ignore_errors=True)
