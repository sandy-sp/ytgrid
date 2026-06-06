import os
import subprocess

from ytgrid.optimizer.tmp_cleaner import clean_tmp_directories
from ytgrid.optimizer.system_monitor import get_system_resources, SystemResources
from ytgrid.optimizer.zombie_reaper import ZombieReaper, _get_ppid
from ytgrid.backend.process_registry import ProcessRegistry


# --- TmpCleaner -------------------------------------------------------

def test_tmp_cleaner_removes_old_prefixed_dirs(tmp_path):
    old = tmp_path / "ytgrid_old"
    old.mkdir()
    keep = tmp_path / "other_dir"
    keep.mkdir()
    result = clean_tmp_directories(tmp_dir=str(tmp_path), prefix="ytgrid_", max_age=0)
    assert result["cleaned"] == 1
    assert not old.exists()
    assert keep.exists()  # non-prefixed dir is never touched


def test_tmp_cleaner_skips_fresh_dirs(tmp_path):
    fresh = tmp_path / "ytgrid_fresh"
    fresh.mkdir()
    result = clean_tmp_directories(tmp_dir=str(tmp_path), prefix="ytgrid_", max_age=9999)
    assert result["skipped"] == 1
    assert fresh.exists()


def test_tmp_cleaner_missing_dir():
    result = clean_tmp_directories(tmp_dir="/nonexistent/path/xyz", max_age=0)
    assert result == {"cleaned": 0, "failed": 0, "skipped": 0}


# --- SystemMonitor ----------------------------------------------------

def test_system_resources_in_range():
    res = get_system_resources()
    assert isinstance(res, SystemResources)
    for value in (res.cpu_percent, res.memory_percent, res.disk_percent):
        assert 0.0 <= value <= 100.0


def test_system_resources_health_logic():
    healthy = SystemResources(10.0, 10.0, 10.0, 50)
    assert healthy.is_healthy is True
    assert healthy.should_throttle is False

    loaded = SystemResources(95.0, 95.0, 95.0, 50)
    assert loaded.is_healthy is False
    assert loaded.should_throttle is True


# --- ZombieReaper -----------------------------------------------------

def test_get_ppid_matches_os():
    assert _get_ppid(os.getpid()) == os.getppid()


def test_zombie_reaper_returns_stats_without_killing(monkeypatch):
    killed = []
    # Never actually signal processes during the test.
    monkeypatch.setattr(
        "ytgrid.optimizer.zombie_reaper.os.kill",
        lambda pid, sig: killed.append(pid),
    )
    stats = ZombieReaper(set()).reap()
    assert set(stats.keys()) == {"found", "killed", "skipped", "errors"}
    assert stats["killed"] == len(killed)


# --- ProcessRegistry --------------------------------------------------

def test_process_registry_register_unregister():
    reg = ProcessRegistry()
    reg.register(111)
    reg.register(222)
    assert reg.get_active_pids() == {111, 222}
    reg.unregister(111)
    assert reg.get_active_pids() == {222}


def test_process_registry_kill_all_handles_dead_pids():
    finished = subprocess.Popen(["true"])
    finished.wait()  # process is now dead, pid no longer signalable
    reg = ProcessRegistry()
    reg.register(finished.pid)
    assert reg.kill_all() == 0
    assert reg.get_active_pids() == set()
