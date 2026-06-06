import random
import threading
from datetime import datetime, timedelta
from typing import List, Optional
from ytgrid.proxy.models import Proxy, ProxyHealth
from ytgrid.utils.config import config

class ProxyPool:
    """Thread-safe proxy pool with weighted selection and cooldown management."""

    def __init__(
        self,
        proxies: List[Proxy] = None,
    ):
        self._proxies = proxies or []
        self._lock = threading.RLock()
        self._cooldown_seconds = config.PROXY_COOLDOWN_SECONDS
        self._max_failure_rate = config.PROXY_MAX_FAILURE_RATE

    def get_proxy(self) -> Optional[Proxy]:
        """
        Select the best available proxy using weighted random selection.
        """
        with self._lock:
            if not self._proxies:
                return None

            now = datetime.now()
            available = [
                p for p in self._proxies
                if p.health in (ProxyHealth.HEALTHY, ProxyHealth.DEGRADED)
                and p.failure_rate < self._max_failure_rate
                and (p.cooldown_until is None or now > p.cooldown_until)
            ]
            if not available:
                # Emergency: return any proxy that isn't totally dead
                available = [p for p in self._proxies if p.health != ProxyHealth.UNHEALTHY]

            if not available:
                return None  # All proxies exhausted

            # Weighted selection: score = 1 / (latency_ms + 1) * (1 - failure_rate)
            weights = []
            for p in available:
                latency_weight = 1.0 / (p.latency_ms + 1.0)
                reliability_weight = 1.0 - p.failure_rate
                idle_bonus = 1.0
                if p.last_used:
                    idle_seconds = (now - p.last_used).total_seconds()
                    idle_bonus = min(idle_seconds / 60.0, 5.0)  # Cap at 5x bonus
                weights.append(max(0.01, latency_weight * reliability_weight * idle_bonus))

            selected = random.choices(available, weights=weights, k=1)[0]
            selected.last_used = datetime.now()
            selected.cooldown_until = datetime.now() + timedelta(seconds=self._cooldown_seconds)
            return selected

    def report_success(self, proxy: Proxy) -> None:
        if not proxy: return
        with self._lock:
            proxy.success_count += 1
            if proxy.health == ProxyHealth.DEGRADED and proxy.failure_rate < 0.1:
                proxy.health = ProxyHealth.HEALTHY

    def report_failure(self, proxy: Proxy) -> None:
        if not proxy: return
        with self._lock:
            proxy.failure_count += 1
            if proxy.failure_rate > self._max_failure_rate:
                proxy.health = ProxyHealth.UNHEALTHY

    def add_proxies(self, new_proxies: List[Proxy]) -> int:
        with self._lock:
            existing_keys = {(p.host, p.port) for p in self._proxies}
            added = 0
            for p in new_proxies:
                if (p.host, p.port) not in existing_keys:
                    self._proxies.append(p)
                    added += 1
            return added

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "total": len(self._proxies),
                "healthy": sum(1 for p in self._proxies if p.health == ProxyHealth.HEALTHY),
                "degraded": sum(1 for p in self._proxies if p.health == ProxyHealth.DEGRADED),
                "unhealthy": sum(1 for p in self._proxies if p.health == ProxyHealth.UNHEALTHY),
                "cooldown": sum(1 for p in self._proxies if p.health == ProxyHealth.COOLDOWN),
            }

proxy_pool = ProxyPool()
