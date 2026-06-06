import os
import signal
from typing import Set

class ProcessRegistry:
    """Track PIDs of Chrome processes spawned by YTGrid."""

    def __init__(self):
        self._pids: Set[int] = set()

    def register(self, pid: int) -> None:
        self._pids.add(pid)

    def unregister(self, pid: int) -> None:
        self._pids.discard(pid)

    def get_active_pids(self) -> Set[int]:
        return self._pids


    def kill_all(self) -> int:
        """Kill only YTGrid-owned processes. Returns count of killed processes."""
        killed = 0
        for pid in list(self._pids):
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except ProcessLookupError:
                pass  # Already dead
            finally:
                self._pids.discard(pid)
        return killed

    def cleanup_zombies(self) -> None:
        """Reap zombie child processes."""
        stale = set()
        for pid in self._pids:
            try:
                os.kill(pid, 0)  # Check if process exists
            except ProcessLookupError:
                stale.add(pid)
        self._pids -= stale

# Global registry
process_registry = ProcessRegistry()
