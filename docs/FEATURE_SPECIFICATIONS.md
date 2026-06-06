# YTGrid Feature Specifications

> **Version:** 3.1.0 (Proposed)
> **Date:** 2026-04-17
> **Author:** Senior Staff Architect

---

## Table of Contents

1. [Auto-Proxy Rotation System](#1-auto-proxy-rotation-system)
2. [Headless Resource Optimizer](#2-headless-resource-optimizer)
3. [User Profiles & Persistence Layer](#3-user-profiles--persistence-layer)

---

## 1. Auto-Proxy Rotation System

### 1.1 Overview

The proxy rotation system intercepts every Selenium session and routes it through a rotating proxy, preventing IP-based rate limiting and detection. The system supports multiple proxy sources (free lists, paid API providers, SOCKS5) and implements health-checking with automatic failover.

### 1.2 Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  TaskManager │────▶│  ProxyMiddleware  │────▶│   ProxyPool     │
│              │     │  (per-session)    │     │   (singleton)   │
└──────────────┘     └────────┬─────────┘     └────────┬────────┘
                              │                        │
                    ┌─────────▼──────────┐   ┌─────────▼────────┐
                    │  Selenium Chrome    │   │  HealthChecker   │
                    │  --proxy-server=... │   │  (background)    │
                    └────────────────────┘   └──────────────────┘
```

### 1.3 Sub-Component Decomposition (LtM Phase 1)

#### Sub-step 1: Proxy Data Model

```python
# ytgrid/proxy/models.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional

class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"       # Latency > threshold but functional
    UNHEALTHY = "unhealthy"     # Failed health check
    COOLDOWN = "cooldown"       # Recently used, resting to avoid detection

@dataclass
class Proxy:
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    health: ProxyHealth = ProxyHealth.HEALTHY
    latency_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    country: Optional[str] = None

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol.value}://{auth}{self.host}:{self.port}"

    @property
    def failure_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.failure_count / total if total > 0 else 0.0
```

#### Sub-step 2: Proxy Pool Manager

```python
# ytgrid/proxy/pool.py
import random
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional
from ytgrid.proxy.models import Proxy, ProxyHealth

class ProxyPool:
    """Thread-safe proxy pool with weighted selection and cooldown management."""

    def __init__(
        self,
        proxies: List[Proxy],
        cooldown_seconds: int = 300,
        max_failure_rate: float = 0.3,
        health_check_interval: int = 60,
    ):
        self._proxies = proxies
        self._lock = threading.Lock()
        self._cooldown_seconds = cooldown_seconds
        self._max_failure_rate = max_failure_rate
        self._health_check_interval = health_check_interval

    def get_proxy(self) -> Optional[Proxy]:
        """
        Select the best available proxy using weighted random selection.

        Weights are inversely proportional to:
        - Failure rate (lower is better)
        - Latency (lower is better)
        - Recency of use (longer idle is better)
        """
        with self._lock:
            available = [
                p for p in self._proxies
                if p.health in (ProxyHealth.HEALTHY, ProxyHealth.DEGRADED)
                and p.failure_rate < self._max_failure_rate
                and (p.cooldown_until is None or datetime.now() > p.cooldown_until)
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
                    idle_seconds = (datetime.now() - p.last_used).total_seconds()
                    idle_bonus = min(idle_seconds / 60.0, 5.0)  # Cap at 5x bonus
                weights.append(latency_weight * reliability_weight * idle_bonus)

            selected = random.choices(available, weights=weights, k=1)[0]
            selected.last_used = datetime.now()
            selected.cooldown_until = datetime.now() + timedelta(seconds=self._cooldown_seconds)
            return selected

    def report_success(self, proxy: Proxy) -> None:
        with self._lock:
            proxy.success_count += 1
            if proxy.health == ProxyHealth.DEGRADED and proxy.failure_rate < 0.1:
                proxy.health = ProxyHealth.HEALTHY

    def report_failure(self, proxy: Proxy) -> None:
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
```

#### Sub-step 3: Health Checker (Background Thread)

```python
# ytgrid/proxy/health.py
import threading
import time
import requests
from ytgrid.proxy.models import Proxy, ProxyHealth
from ytgrid.proxy.pool import ProxyPool
from ytgrid.utils.logger import log_info, log_error

HEALTH_CHECK_URL = "https://httpbin.org/ip"
HEALTH_CHECK_TIMEOUT = 10  # seconds
LATENCY_DEGRADED_THRESHOLD = 5000  # ms

class ProxyHealthChecker:
    """Background daemon that periodically validates proxy health."""

    def __init__(self, pool: ProxyPool, interval: int = 60):
        self._pool = pool
        self._interval = interval
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
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
        for proxy in self._pool._proxies:
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
            proxy.latency_ms = latency
            if resp.status_code == 200:
                proxy.health = (
                    ProxyHealth.DEGRADED if latency > LATENCY_DEGRADED_THRESHOLD
                    else ProxyHealth.HEALTHY
                )
            else:
                proxy.health = ProxyHealth.UNHEALTHY
        except Exception:
            proxy.health = ProxyHealth.UNHEALTHY
```

#### Sub-step 4: Integration with `browser.py`

```python
# Modified get_browser() to accept a proxy
def get_browser(
    user_data_dir: Optional[str] = None,
    proxy: Optional["Proxy"] = None
) -> Tuple[webdriver.Chrome, WebDriverWait]:
    options = Options()
    # ... existing flags ...

    # Inject proxy if provided
    if proxy:
        options.add_argument(f"--proxy-server={proxy.url}")
        if proxy.username:
            # For authenticated proxies, use a Chrome extension
            # (Selenium doesn't natively support proxy auth in headless)
            _inject_proxy_auth_extension(options, proxy)

    # ... rest of function ...
```

#### Sub-step 5: Proxy Source Loaders

```python
# ytgrid/proxy/sources.py
from typing import List
from ytgrid.proxy.models import Proxy, ProxyProtocol

class ProxySource:
    """Abstract base for proxy providers."""
    def fetch(self) -> List[Proxy]: ...

class FileProxySource(ProxySource):
    """Load proxies from a local file (host:port:user:pass per line)."""
    def __init__(self, filepath: str): ...

class EnvProxySource(ProxySource):
    """Load proxies from YTGRID_PROXY_LIST environment variable."""
    def __init__(self): ...

class APIProxySource(ProxySource):
    """Fetch proxies from a paid provider API (e.g., ProxyScrape, BrightData)."""
    def __init__(self, api_url: str, api_key: str): ...
```

### 1.4 Configuration

```bash
# .env additions
YTGRID_PROXY_ENABLED=True
YTGRID_PROXY_SOURCE=file                  # file | env | api
YTGRID_PROXY_FILE=./proxies.txt
YTGRID_PROXY_API_URL=
YTGRID_PROXY_API_KEY=
YTGRID_PROXY_COOLDOWN_SECONDS=300
YTGRID_PROXY_HEALTH_CHECK_INTERVAL=60
YTGRID_PROXY_MAX_FAILURE_RATE=0.3
```

### 1.5 Identified Bottlenecks & Mitigations

| Bottleneck | Impact | Mitigation |
|-----------|--------|------------|
| Health check blocking all proxies simultaneously | Delayed proxy availability | Check proxies in batches of 10 with 1s delay between batches |
| Thread contention on `ProxyPool._lock` | Latency spike under high concurrency | Use `threading.RLock` and minimize lock scope; separate read/write locks |
| Proxy auth extension injection for headless Chrome | Extension loading is unreliable in headless | Fall back to `selenium-wire` for proxy auth, or use an upstream proxy (e.g., `mitmproxy`) as a local forwarder |

---

## 2. Headless Resource Optimizer

### 2.1 Overview

The Resource Optimizer is a background service that prevents system degradation by:
1. **Cleaning orphaned `/tmp/ytgrid_*` directories** from crashed browser sessions.
2. **Killing zombie Chrome/chromedriver processes** that were not properly terminated.
3. **Monitoring system resource consumption** and throttling new sessions when resources are low.

### 2.2 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   ResourceOptimizer                       │
│                                                           │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ TmpCleaner      │  │ ZombieReaper │  │ SystemMonitor│ │
│  │ (cron: 5min)    │  │ (cron: 1min) │  │ (cron: 30s)  │ │
│  └────────┬────────┘  └──────┬───────┘  └──────┬───────┘ │
│           │                  │                  │         │
│           └──────────────────┼──────────────────┘         │
│                              │                            │
│                    ┌─────────▼──────────┐                 │
│                    │  ProcessRegistry   │                 │
│                    │  (PID tracking)    │                 │
│                    └───────────────────┘                 │
└──────────────────────────────────────────────────────────┘
```

### 2.3 Sub-Component Decomposition (LtM Phase 1)

#### Decision: Background Thread vs. Celery Beat vs. System Cron

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Background Thread** | No external deps; runs in-process | Dies if main process dies; single-instance only | ✅ **Selected for dev/single-node** |
| **Celery Beat** | Distributed; survives restarts | Requires Redis; over-engineered for cleanup | Use when Celery is already active |
| **System Cron** | Survives everything; OS-native | External config; Docker complexity | Use in production Docker |

**Recommendation:** Implement as a background thread with an optional Celery Beat schedule.

#### Sub-step 1: TmpCleaner

```python
# ytgrid/optimizer/tmp_cleaner.py
import os
import shutil
import time
from pathlib import Path
from ytgrid.utils.logger import log_info, log_error

# Only clean directories matching this prefix
YTGRID_TMP_PREFIX = "ytgrid_"
# Clean dirs older than this (seconds)
MAX_AGE_SECONDS = 1800  # 30 minutes

def clean_tmp_directories(
    tmp_dir: str = "/tmp",
    prefix: str = YTGRID_TMP_PREFIX,
    max_age: int = MAX_AGE_SECONDS,
) -> dict:
    """
    Remove stale YTGrid temporary directories from /tmp.

    Returns a dict with counts of cleaned and failed directories.
    """
    cleaned = 0
    failed = 0
    skipped = 0
    now = time.time()

    for entry in Path(tmp_dir).iterdir():
        if not entry.is_dir():
            continue
        if not entry.name.startswith(prefix):
            continue

        age = now - entry.stat().st_mtime
        if age < max_age:
            skipped += 1
            continue

        try:
            shutil.rmtree(entry)
            cleaned += 1
            log_info(f"Cleaned stale tmp dir: {entry} (age: {age:.0f}s)")
        except Exception as e:
            failed += 1
            log_error(f"Failed to clean {entry}: {e}")

    return {"cleaned": cleaned, "failed": failed, "skipped": skipped}
```

#### Sub-step 2: ZombieReaper

```python
# ytgrid/optimizer/zombie_reaper.py
import os
import signal
from typing import Set, Dict
from ytgrid.utils.logger import log_info, log_error

class ZombieReaper:
    """
    Kill Chrome/chromedriver processes that are NOT registered in the ProcessRegistry.

    SAFETY: Only kills processes that:
    1. Match known Chrome binary paths
    2. Were started by the current user (UID match)
    3. Have been running longer than the grace period
    """

    CHROME_PROCESS_NAMES = {"chrome", "chromedriver", "google-chrome"}
    GRACE_PERIOD_SECONDS = 600  # 10 minutes before considering it a zombie

    def __init__(self, registered_pids: Set[int]):
        self._registered = registered_pids

    def reap(self) -> Dict[str, int]:
        """Find and kill zombie browser processes. Returns stats."""
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

                # Check UID (only kill our own processes)
                stat = os.stat(f"/proc/{pid}")
                if stat.st_uid != current_uid:
                    stats["skipped"] += 1
                    continue

                # Check age
                import time
                uptime = time.time() - stat.st_ctime
                if uptime < self.GRACE_PERIOD_SECONDS:
                    stats["skipped"] += 1
                    continue

                stats["found"] += 1
                os.kill(pid, signal.SIGTERM)
                stats["killed"] += 1
                log_info(f"Reaped zombie Chrome process PID={pid} (age={uptime:.0f}s)")

            except (FileNotFoundError, PermissionError):
                continue  # Process disappeared or not ours
            except Exception as e:
                stats["errors"] += 1
                log_error(f"Error reaping PID={pid}: {e}")

        return stats
```

#### Sub-step 3: System Resource Monitor

```python
# ytgrid/optimizer/system_monitor.py
import os
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

def _read_cpu_usage() -> float:
    """Parse /proc/stat for CPU usage percentage."""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:])
        return round((1 - idle / total) * 100, 1) if total > 0 else 0.0
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
```

#### Sub-step 4: Orchestrator

```python
# ytgrid/optimizer/orchestrator.py
import threading
import time
from ytgrid.optimizer.tmp_cleaner import clean_tmp_directories
from ytgrid.optimizer.zombie_reaper import ZombieReaper
from ytgrid.optimizer.system_monitor import get_system_resources
from ytgrid.utils.logger import log_info

class ResourceOptimizer:
    """
    Background daemon that runs cleanup and monitoring tasks on schedules.

    Schedules:
    - TmpCleaner:     every 5 minutes
    - ZombieReaper:   every 1 minute
    - SystemMonitor:  every 30 seconds
    """

    def __init__(self, registered_pids: set):
        self._registered_pids = registered_pids
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._throttle_active = False

    @property
    def is_throttled(self) -> bool:
        return self._throttle_active

    def start(self) -> None:
        schedules = [
            ("TmpCleaner", self._run_tmp_cleaner, 300),
            ("ZombieReaper", self._run_zombie_reaper, 60),
            ("SystemMonitor", self._run_system_monitor, 30),
        ]
        for name, func, interval in schedules:
            t = threading.Thread(target=self._loop, args=(name, func, interval), daemon=True)
            t.start()
            self._threads.append(t)
        log_info("ResourceOptimizer started with 3 background tasks.")

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=5)

    def _loop(self, name: str, func, interval: int) -> None:
        while not self._stop_event.is_set():
            try:
                func()
            except Exception as e:
                from ytgrid.utils.logger import log_error
                log_error(f"ResourceOptimizer/{name} error: {e}")
            self._stop_event.wait(timeout=interval)

    def _run_tmp_cleaner(self) -> None:
        result = clean_tmp_directories()
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
```

### 2.4 Integration with TaskManager

```python
# In task_manager.py, modify start_session:
def start_session(self, ...):
    # Check resource throttle before starting
    if self.optimizer.is_throttled:
        log_info(f"Session {session_id} queued: system resources under pressure.")
        return False  # Or queue for later

    # ...existing logic...
```

### 2.5 Identified Bottlenecks & Mitigations

| Bottleneck | Impact | Mitigation |
|-----------|--------|------------|
| `/proc` filesystem scanning in ZombieReaper is O(n) over all PIDs | Slow on systems with 10K+ processes | Add a PID cache; only scan delta since last check |
| `shutil.rmtree` on large Chrome profile dirs blocks the thread | TmpCleaner thread becomes unresponsive | Use `shutil.rmtree` in a `ThreadPoolExecutor` with a 10s timeout |
| `os.statvfs` can hang on network-mounted `/tmp` | SystemMonitor freezes | Set a 2-second alarm (`signal.alarm`) as a watchdog |

---

## 3. User Profiles & Persistence Layer

### 3.1 Overview

User Profiles allow operators to save, reload, and share automation configurations. Instead of re-entering URLs, speeds, and loop counts every time, users create named "profiles" that persist across restarts.

### 3.2 Database Schema

**Technology Choice:** SQLite via `aiosqlite` (zero-config, embedded, async-compatible).

```sql
-- ytgrid/database/schema.sql

-- Core profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id              TEXT PRIMARY KEY,           -- UUID
    name            TEXT NOT NULL UNIQUE,        -- Human-readable name
    description     TEXT DEFAULT '',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN DEFAULT TRUE,
    tags            TEXT DEFAULT '[]'            -- JSON array of tags
);

-- Profile entries (individual automation targets)
CREATE TABLE IF NOT EXISTS profile_entries (
    id              TEXT PRIMARY KEY,           -- UUID
    profile_id      TEXT NOT NULL,
    url             TEXT NOT NULL,
    speed           REAL DEFAULT 1.0,
    loop_count      INTEGER DEFAULT 1,
    task_type       TEXT DEFAULT 'video',
    priority        INTEGER DEFAULT 0,          -- Higher = run first
    proxy_group     TEXT DEFAULT NULL,           -- Optional proxy affinity
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Execution history
CREATE TABLE IF NOT EXISTS execution_history (
    id              TEXT PRIMARY KEY,
    profile_id      TEXT NOT NULL,
    entry_id        TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP,
    status          TEXT DEFAULT 'running',      -- running | completed | failed | cancelled
    loops_completed INTEGER DEFAULT 0,
    error_message   TEXT,
    proxy_used      TEXT,                         -- Proxy URL used for this execution
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (entry_id) REFERENCES profile_entries(id)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_entries_profile ON profile_entries(profile_id);
CREATE INDEX IF NOT EXISTS idx_history_profile ON execution_history(profile_id);
CREATE INDEX IF NOT EXISTS idx_history_status ON execution_history(status);
CREATE INDEX IF NOT EXISTS idx_history_started ON execution_history(started_at);
```

### 3.3 Data Access Layer

```python
# ytgrid/database/repository.py
import uuid
import aiosqlite
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

DB_PATH = "ytgrid.db"  # Configurable via env

@dataclass
class Profile:
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    tags: list

@dataclass
class ProfileEntry:
    id: str
    profile_id: str
    url: str
    speed: float
    loop_count: int
    task_type: str
    priority: int

class ProfileRepository:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self._db_path) as db:
            with open("ytgrid/database/schema.sql") as f:
                await db.executescript(f.read())
            await db.commit()

    async def create_profile(self, name: str, description: str = "") -> Profile:
        profile_id = str(uuid.uuid4())
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO profiles (id, name, description) VALUES (?, ?, ?)",
                (profile_id, name, description),
            )
            await db.commit()
        return Profile(
            id=profile_id, name=name, description=description,
            created_at=datetime.now(), updated_at=datetime.now(),
            is_active=True, tags=[],
        )

    async def get_profile(self, name: str) -> Optional[Profile]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM profiles WHERE name = ? AND is_active = 1", (name,)
            )
            row = await cursor.fetchone()
            if row:
                return Profile(**dict(row))
        return None

    async def list_profiles(self) -> List[Profile]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM profiles WHERE is_active = 1 ORDER BY updated_at DESC"
            )
            rows = await cursor.fetchall()
            return [Profile(**dict(r)) for r in rows]

    async def add_entry(
        self, profile_id: str, url: str, speed: float = 1.0,
        loop_count: int = 1, task_type: str = "video", priority: int = 0,
    ) -> ProfileEntry:
        entry_id = str(uuid.uuid4())
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO profile_entries
                   (id, profile_id, url, speed, loop_count, task_type, priority)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (entry_id, profile_id, url, speed, loop_count, task_type, priority),
            )
            await db.commit()
        return ProfileEntry(
            id=entry_id, profile_id=profile_id, url=url,
            speed=speed, loop_count=loop_count, task_type=task_type, priority=priority,
        )

    async def get_entries(self, profile_id: str) -> List[ProfileEntry]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM profile_entries WHERE profile_id = ? ORDER BY priority DESC",
                (profile_id,),
            )
            return [ProfileEntry(**dict(r)) for r in await cursor.fetchall()]

    async def delete_profile(self, profile_id: str) -> bool:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE profiles SET is_active = 0 WHERE id = ?", (profile_id,)
            )
            await db.commit()
        return True

    async def record_execution(
        self, profile_id: str, entry_id: str, session_id: str,
        proxy_used: Optional[str] = None,
    ) -> str:
        exec_id = str(uuid.uuid4())
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO execution_history
                   (id, profile_id, entry_id, session_id, proxy_used)
                   VALUES (?, ?, ?, ?, ?)""",
                (exec_id, profile_id, entry_id, session_id, proxy_used),
            )
            await db.commit()
        return exec_id
```

### 3.4 API Endpoints

```python
# ytgrid/backend/routes/profiles.py (NEW FILE)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from ytgrid.database.repository import ProfileRepository

router = APIRouter()
repo = ProfileRepository()

class CreateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)

class AddEntryRequest(BaseModel):
    url: str
    speed: float = Field(default=1.0, ge=0.25, le=16.0)
    loop_count: int = Field(default=1, ge=1, le=1000)
    task_type: str = "video"
    priority: int = Field(default=0, ge=0, le=100)

@router.post("/", status_code=201)
async def create_profile(request: CreateProfileRequest):
    profile = await repo.create_profile(request.name, request.description)
    return {"profile_id": profile.id, "name": profile.name}

@router.get("/")
async def list_profiles():
    profiles = await repo.list_profiles()
    return {"profiles": [p.__dict__ for p in profiles]}

@router.get("/{name}")
async def get_profile(name: str):
    profile = await repo.get_profile(name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    entries = await repo.get_entries(profile.id)
    return {"profile": profile.__dict__, "entries": [e.__dict__ for e in entries]}

@router.post("/{profile_id}/entries", status_code=201)
async def add_entry(profile_id: str, request: AddEntryRequest):
    entry = await repo.add_entry(
        profile_id, request.url, request.speed,
        request.loop_count, request.task_type, request.priority,
    )
    return {"entry_id": entry.id}

@router.post("/{name}/run")
async def run_profile(name: str):
    """Execute all entries in a profile as automation sessions."""
    profile = await repo.get_profile(name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    entries = await repo.get_entries(profile.id)
    # ... start sessions for each entry ...
    return {"message": f"Started {len(entries)} sessions from profile '{name}'"}
```

### 3.5 CLI Integration

```bash
# New CLI commands:
ytgrid profile create --name "morning-mix" --description "Daily playlist"
ytgrid profile add --name "morning-mix" --url "https://youtube.com/watch?v=..." --loops 5
ytgrid profile list
ytgrid profile run --name "morning-mix"
ytgrid profile export --name "morning-mix" --output profile.json
ytgrid profile import --file profile.json
```

### 3.6 Identified Bottlenecks & Mitigations

| Bottleneck | Impact | Mitigation |
|-----------|--------|------------|
| SQLite single-writer lock under concurrent API requests | 503 errors during parallel profile creation | Use WAL journal mode (`PRAGMA journal_mode=WAL`) for concurrent read/write |
| Opening a new DB connection per-request is expensive | Connection overhead | Use a connection pool (e.g., `databases` library with pool_size=5) |
| `executescript` re-reads schema.sql on every `initialize()` call | I/O on startup | Cache schema in memory; only execute on first run (check table existence first) |
