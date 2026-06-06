import os
import signal
import time
from typing import Set, Dict
from ytgrid.utils.logger import log_info, log_error


def _get_ppid(pid: int) -> int:
    """Return the parent PID of a process by parsing /proc/<pid>/stat.

    The comm field may itself contain spaces or parentheses, so the fields
    after the final ')' are used: state, ppid, ...
    """
    with open(f"/proc/{pid}/stat") as f:
        data = f.read()
    rparen = data.rfind(")")
    fields = data[rparen + 2:].split()
    return int(fields[1])


class ZombieReaper:
    """
    Kill ORPHANED Chrome/chromedriver processes.

    SAFETY: Only kills processes that:
    1. Match known Chrome binary names
    2. Have been re-parented to init (ppid == 1) — i.e. their owning
       session worker is already gone, so they are genuine orphans
    3. Were started by the current user (UID match)
    4. Have been running longer than the grace period

    Chrome instances belonging to an active session keep a live parent
    process, so they are never touched. This makes the reaper safe even
    though the in-memory PID registry is not shared across processes.
    """

    CHROME_PROCESS_NAMES = {"chrome", "chromedriver", "google-chrome"}
    GRACE_PERIOD_SECONDS = 600  # 10 minutes before considering it a zombie

    def __init__(self, registered_pids: Set[int]):
        self._registered = registered_pids

    def reap(self) -> Dict[str, int]:
        """Find and kill orphaned browser processes. Returns stats."""
        stats = {"found": 0, "killed": 0, "skipped": 0, "errors": 0}
        current_uid = os.getuid()

        for pid_dir in os.listdir("/proc"):
            if not pid_dir.isdigit():
                continue
            pid = int(pid_dir)
            if pid in self._registered:
                continue  # Known process, skip

            try:
                # Read process command line
                with open(f"/proc/{pid}/cmdline", "r") as f:
                    cmdline = f.read().replace("\x00", " ").lower()

                # Check if it's a Chrome process
                if not any(name in cmdline for name in self.CHROME_PROCESS_NAMES):
                    continue

                # Only reap genuine orphans (re-parented to init).
                # A Chrome under an active session still has a live parent.
                if _get_ppid(pid) != 1:
                    stats["skipped"] += 1
                    continue

                # Check UID (only kill our own processes)
                stat = os.stat(f"/proc/{pid}")
                if stat.st_uid != current_uid:
                    stats["skipped"] += 1
                    continue

                # Check age
                uptime = time.time() - stat.st_ctime
                if uptime < self.GRACE_PERIOD_SECONDS:
                    stats["skipped"] += 1
                    continue

                stats["found"] += 1
                os.kill(pid, signal.SIGTERM)
                stats["killed"] += 1
                log_info(f"Reaped orphaned browser process PID={pid} (age={uptime:.0f}s)")

            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue  # Process disappeared or not ours
            except Exception as e:
                stats["errors"] += 1
                log_error(f"Error reaping PID={pid}: {e}")

        return stats
