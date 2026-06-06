import os
import time
from dataclasses import dataclass
from ytgrid.utils.logger import log_info, log_error

@dataclass
class SystemResources:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    open_file_descriptors: int

    @property
    def is_healthy(self) -> bool:
        return (
            self.cpu_percent < 85.0
            and self.memory_percent < 85.0
            and self.disk_percent < 90.0
        )

    @property
    def should_throttle(self) -> bool:
        return (
            self.cpu_percent > 70.0
            or self.memory_percent > 70.0
            or self.disk_percent > 80.0
        )

def get_system_resources() -> SystemResources:
    """
    Gather system resource usage WITHOUT psutil dependency.
    Uses /proc filesystem (Linux only).
    """
    # CPU: read /proc/stat
    cpu_percent = _read_cpu_usage()

    # Memory: read /proc/meminfo
    memory_percent = _read_memory_usage()

    # Disk: os.statvfs
    disk_percent = _read_disk_usage("/tmp")

    # File descriptors
    try:
        fd_count = len(os.listdir(f"/proc/{os.getpid()}/fd"))
    except Exception:
        fd_count = -1

    return SystemResources(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        open_file_descriptors=fd_count,
    )

def _read_cpu_times() -> tuple[int, int]:
    """Return (idle, total) jiffies from the aggregate /proc/stat line."""
    with open("/proc/stat") as f:
        line = f.readline()
    values = [int(p) for p in line.split()[1:]]
    # Fields: user nice system idle iowait irq softirq steal guest guest_nice
    idle = values[3] + (values[4] if len(values) > 4 else 0)  # idle + iowait
    total = sum(values)
    return idle, total


def _read_cpu_usage(sample_interval: float = 0.1) -> float:
    """Sample /proc/stat twice and return instantaneous CPU usage percentage.

    A single read only yields the cumulative average since boot, which never
    reflects current load. Two samples over a short window give a live value.
    """
    try:
        idle1, total1 = _read_cpu_times()
        time.sleep(sample_interval)
        idle2, total2 = _read_cpu_times()
        idle_delta = idle2 - idle1
        total_delta = total2 - total1
        if total_delta <= 0:
            return 0.0
        return round((1 - idle_delta / total_delta) * 100, 1)
    except Exception:
        return 0.0

def _read_memory_usage() -> float:
    """Parse /proc/meminfo for memory usage percentage."""
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, val = line.split(":")
                info[key.strip()] = int(val.strip().split()[0])
        total = info.get("MemTotal", 1)
        available = info.get("MemAvailable", total)
        return round((1 - available / total) * 100, 1)
    except Exception:
        return 0.0

def _read_disk_usage(path: str) -> float:
    """Use os.statvfs for disk usage."""
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        return round((1 - free / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        return 0.0
