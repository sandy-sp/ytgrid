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

    tmp_path = Path(tmp_dir)
    if not tmp_path.exists():
        return {"cleaned": 0, "failed": 0, "skipped": 0}

    for entry in tmp_path.iterdir():
        if not entry.is_dir():
            continue
        if not entry.name.startswith(prefix):
            continue

        try:
            age = now - entry.stat().st_mtime
            if age < max_age:
                skipped += 1
                continue
        except FileNotFoundError:
            continue

        try:
            shutil.rmtree(entry)
            cleaned += 1
            log_info(f"Cleaned stale tmp dir: {entry} (age: {age:.0f}s)")
        except Exception as e:
            failed += 1
            log_error(f"Failed to clean {entry}: {e}")

    return {"cleaned": cleaned, "failed": failed, "skipped": skipped}
