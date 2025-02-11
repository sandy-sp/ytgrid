"""
Celery Tasks Module (Version 3)

This module defines Celery tasks for automation. The task 'run_automation'
executes the automation player for a given session.
"""

from typing import Any
from ytgrid.backend.celery_app import celery_app
from ytgrid.backend.task_manager import AUTOMATION_PLAYERS
from ytgrid.utils.logger import log_info, log_error

@celery_app.task(name="ytgrid.tasks.run_automation")
def run_automation(session_id: str, url: str, speed: float, loop_count: int, task_type: str) -> str:
    """
    Celery task to run automation using the selected automation player.

    :param session_id: Unique identifier for the session.
    :param url: YouTube video URL.
    :param speed: Playback speed multiplier.
    :param loop_count: Total number of loops to execute.
    :param task_type: Type of automation task.
    :return: "completed" if all loops execute successfully, "error" otherwise.
    """
    player_class: Any = AUTOMATION_PLAYERS.get(task_type)
    if not player_class:
        log_error(f"Unsupported task type: {task_type}")
        return "error"

    for loop in range(loop_count):
        log_info(f"Celery Task - Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} using '{task_type}' automation.")
        try:
            player_instance = player_class()
            # Each iteration plays one loop.
            player_instance.play_video(url, speed, 1)
        except Exception as e:
            log_error(f"Celery Task - Session {session_id}: Loop {loop + 1} encountered error: {e}")
            return "error"

    log_info(f"Celery Task - Session {session_id}: All {loop_count} loops completed.")
    return "completed"
