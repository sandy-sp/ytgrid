import multiprocessing
import os
from ytgrid.utils.logger import log_info, log_error
from ytgrid.automation.player import VideoPlayer  # Concrete automation player
from ytgrid.utils.config import config

# Mapping from task type to automation player class.
AUTOMATION_PLAYERS = {
    "video": VideoPlayer,
    # Future expansion: "batch": BatchPlayer, "channel": ChannelPlayer, etc.
}

class TaskManager:
    """Manages concurrent automation sessions using either multiprocessing or Celery."""

    def __init__(self):
        # For multiprocessing: {session_id: Process} and loop counts.
        # For Celery: {session_id: AsyncResult}
        self.processes = {}
        self.loop_counts = {}

    def start_session(self, session_id, url, speed, loop_count, task_type="video"):
        """Starts a new automation session."""
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False

        log_info(f"Starting session {session_id} for {url} with {loop_count} loops (task_type: {task_type}).")
        if config.USE_CELERY:
            # Use Celery to process the task asynchronously.
            from ytgrid.backend.celery_app import celery_app
            task = celery_app.send_task("ytgrid.tasks.run_automation", args=(session_id, url, speed, loop_count, task_type))
            self.processes[session_id] = task
            log_info(f"Celery Task {session_id} started. Task ID: {task.id}")
            return True
        else:
            # Use multiprocessing.
            loop_counter = multiprocessing.Value('i', 0)
            self.loop_counts[session_id] = loop_counter
            process = multiprocessing.Process(
                target=self._start_process,
                args=(session_id, url, speed, loop_count, loop_counter, task_type)
            )
            process.daemon = True
            process.start()
            self.processes[session_id] = process
            return True

    @staticmethod
    def _start_process(session_id, url, speed, loop_count, loop_counter, task_type):
        os.environ["PYTHONWARNINGS"] = "ignore"
        task_manager.run_automation(session_id, url, speed, loop_count, loop_counter, task_type)

    def run_automation(self, session_id, url, speed, loop_count, loop_counter, task_type):
        """Runs automation using the selected automation player (multiprocessing branch)."""
        player_class = AUTOMATION_PLAYERS.get(task_type)
        if not player_class:
            log_error(f"Unsupported task type: {task_type}")
            return

        for loop in range(loop_count):
            loop_counter.value = loop + 1
            log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} using '{task_type}' automation.")
            player_instance = player_class()
            player_instance.play_video(url, speed, 1)
        log_info(f"Session {session_id}: All {loop_count} loops completed.")
        if session_id in self.loop_counts:
            del self.loop_counts[session_id]

    def stop_session(self, session_id):
        """Stops an active session."""
        if session_id in self.processes:
            if config.USE_CELERY:
                # Attempt to revoke the Celery task.
                task = self.processes[session_id]
                task.revoke(terminate=True)
                log_info(f"Celery Task {session_id} revoked.")
            else:
                self.processes[session_id].terminate()
                self.processes[session_id].join()
                if session_id in self.loop_counts:
                    del self.loop_counts[session_id]
                log_info(f"Session {session_id} stopped.")
                os.system("pkill -f chromedriver")
                os.system("pkill -f chrome")
            del self.processes[session_id]
            return True
        return False

    def get_active_sessions(self):
        """Returns a list of active sessions with their current progress/status."""
        active_sessions = []
        for session_id, proc in self.processes.items():
            if config.USE_CELERY:
                # Celery tasks provide a status string (e.g., 'PENDING', 'SUCCESS').
                status = proc.status
                active_sessions.append({"id": session_id, "status": status})
            else:
                loop = self.loop_counts[session_id].value if session_id in self.loop_counts else 0
                active_sessions.append({"id": session_id, "loop": loop})
        return active_sessions

# Global task manager instance.
task_manager = TaskManager()
