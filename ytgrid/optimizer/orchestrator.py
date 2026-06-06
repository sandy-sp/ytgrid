import threading
import time
from typing import Set

from ytgrid.optimizer.tmp_cleaner import clean_tmp_directories
from ytgrid.optimizer.zombie_reaper import ZombieReaper
from ytgrid.optimizer.system_monitor import get_system_resources
from ytgrid.utils.logger import log_info, log_error
from ytgrid.utils.config import config

class ResourceOptimizer:
    """
    Background daemon that runs cleanup and monitoring tasks on schedules.
    """

    def __init__(self, registered_pids: Set[int]):
        self._registered_pids = registered_pids
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._throttle_active = False

    @property
    def is_throttled(self) -> bool:
        if not config.OPTIMIZER_ENABLED:
            return False
        return self._throttle_active

    def start(self) -> None:
        if not config.OPTIMIZER_ENABLED:
            log_info("ResourceOptimizer is disabled via config.")
            return

        schedules = [
            ("TmpCleaner", self._run_tmp_cleaner, 300),
            ("ZombieReaper", self._run_zombie_reaper, 60),
            ("SystemMonitor", self._run_system_monitor, 30),
        ]
        for name, func, interval in schedules:
            t = threading.Thread(target=self._loop, args=(name, func, interval), daemon=True)
            t.start()
            self._threads.append(t)
        log_info("ResourceOptimizer started with background tasks.")

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=5)

    def _loop(self, name: str, func, interval: int) -> None:
        while not self._stop_event.is_set():
            try:
                func()
            except Exception as e:
                log_error(f"ResourceOptimizer/{name} error: {e}")
            self._stop_event.wait(timeout=interval)

    def _run_tmp_cleaner(self) -> None:
        result = clean_tmp_directories(max_age=config.TMP_MAX_AGE)
        if result["cleaned"] > 0:
            log_info(f"TmpCleaner: cleaned={result['cleaned']}, failed={result['failed']}")

    def _run_zombie_reaper(self) -> None:
        reaper = ZombieReaper(self._registered_pids)
        result = reaper.reap()
        if result["killed"] > 0:
            log_info(f"ZombieReaper: killed={result['killed']}, found={result['found']}")

    def _run_system_monitor(self) -> None:
        resources = get_system_resources()
        self._throttle_active = resources.should_throttle
        if not resources.is_healthy:
            log_info(
                f"SystemMonitor WARNING: CPU={resources.cpu_percent}%, "
                f"MEM={resources.memory_percent}%, DISK={resources.disk_percent}%"
            )

# Create a global instance that will be bound to process_registry later
from ytgrid.backend.process_registry import process_registry
optimizer = ResourceOptimizer(process_registry.get_active_pids())
