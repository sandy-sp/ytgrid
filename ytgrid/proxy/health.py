import threading
import time
import requests
from ytgrid.proxy.models import Proxy, ProxyHealth
from ytgrid.proxy.pool import proxy_pool
from ytgrid.utils.logger import log_info, log_error
from ytgrid.utils.config import config

HEALTH_CHECK_URL = "https://httpbin.org/ip"
HEALTH_CHECK_TIMEOUT = 10  # seconds
LATENCY_DEGRADED_THRESHOLD = 5000  # ms

class ProxyHealthChecker:
    """Background daemon that periodically validates proxy health."""

    def __init__(self, interval: int = 60):
        self._interval = config.PROXY_HEALTH_CHECK_INTERVAL or interval
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if not config.PROXY_ENABLED:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log_info("ProxyHealthChecker started.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._check_all()
            self._stop_event.wait(timeout=self._interval)

    def _check_all(self) -> None:
        # Avoid thread lock contention during the check delay; copy the list
        with proxy_pool._lock:
            proxies_copy = list(proxy_pool._proxies)

        for proxy in proxies_copy:
            if self._stop_event.is_set():
                break
            self._check_one(proxy)

    def _check_one(self, proxy: Proxy) -> None:
        try:
            start = time.monotonic()
            resp = requests.get(
                HEALTH_CHECK_URL,
                proxies={"http": proxy.url, "https": proxy.url},
                timeout=HEALTH_CHECK_TIMEOUT,
            )
            latency = (time.monotonic() - start) * 1000

            with proxy_pool._lock:
                proxy.latency_ms = latency
                if resp.status_code == 200:
                    proxy.health = (
                        ProxyHealth.DEGRADED if latency > LATENCY_DEGRADED_THRESHOLD
                        else ProxyHealth.HEALTHY
                    )
                else:
                    proxy.health = ProxyHealth.UNHEALTHY
        except Exception:
            with proxy_pool._lock:
                proxy.health = ProxyHealth.UNHEALTHY
