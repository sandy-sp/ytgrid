from ytgrid.backend.celery_app import celery_app
from ytgrid.backend.task_manager import AUTOMATION_PLAYERS
from ytgrid.utils.logger import log_info, log_error

@celery_app.task(name="ytgrid.tasks.run_automation")
def run_automation(session_id, url, speed, loop_count, task_type):
    """
    Celery task to run automation using the selected automation player.
    """
    player_class = AUTOMATION_PLAYERS.get(task_type)
    if not player_class:
        log_error(f"Unsupported task type: {task_type}")
        return "error"
    
    for loop in range(loop_count):
        log_info(f"Celery Task - Session {session_id}: Loop {loop+1}/{loop_count} - Playing {url} using '{task_type}' automation.")
        player_instance = player_class()
        # Each call plays one loop.
        player_instance.play_video(url, speed, 1)
    
    log_info(f"Celery Task - Session {session_id}: All {loop_count} loops completed.")
    return "completed"
