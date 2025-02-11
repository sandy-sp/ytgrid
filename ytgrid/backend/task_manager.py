import multiprocessing
import os
from typing import Dict, Union, Any, List

from ytgrid.utils.logger import log_info, log_error
from ytgrid.automation.player import VideoPlayer
from ytgrid.utils.config import config

# Mapping from task type to automation player class.
AUTOMATION_PLAYERS: Dict[str, Any] = {
    "video": VideoPlayer,
    # Future expansion: "batch": BatchPlayer, "channel": ChannelPlayer, etc.
}

def kill_browser_processes() -> None:
    """
    Kill stray browser and chromedriver processes to free up system resources.
    """
    os.system("pkill -f chromedriver")
    os.system("pkill -f chrome")


class TaskManager:
    """
    Manages automation sessions using either multiprocessing or Celery.
    Future enhancements include dynamic scheduling based on system resource usage (see :contentReference[oaicite:1]{index=1}).
    """
    def __init__(self) -> None:
        self.processes: Dict[str, Union[multiprocessing.Process, Any]] = {}  # {session_id: Process or Celery Task}
        self.loop_counts: Dict[str, multiprocessing.Value] = {}  # {session_id: multiprocessing.Value}

    def start_session(
        self,
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        task_type: str = "video",
        use_celery: Union[bool, None] = None
    ) -> bool:
        """
        Starts an automation session.
        :param session_id: Unique identifier for the session.
        :param url: URL of the video to be played.
        :param speed: Playback speed.
        :param loop_count: Total number of loops to run.
        :param task_type: Type of automation task (default "video").
        :param use_celery: Optional flag to override the default Celery setting.
        :return: True if the session is started successfully, False otherwise.
        """
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False

        log_info(f"Starting session {session_id} for {url} with {loop_count} loops (task_type: {task_type}).")
        use_celery = config.USE_CELERY if use_celery is None else use_celery

        if use_celery:
            from ytgrid.backend.celery_app import celery_app
            task = celery_app.send_task(
                "ytgrid.tasks.run_automation", args=(session_id, url, speed, loop_count, task_type)
            )
            self.processes[session_id] = task
            log_info(f"Celery Task {session_id} started. Task ID: {task.id}")
            return True
        else:
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
    def _start_process(
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        loop_counter: multiprocessing.Value,
        task_type: str
    ) -> None:
        """
        Static helper to run automation in a separate process.
        """
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Invokes the global task_manager's run_automation method.
        task_manager.run_automation(session_id, url, speed, loop_count, loop_counter, task_type)

    def run_automation(
        self,
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        loop_counter: multiprocessing.Value,
        task_type: str
    ) -> None:
        """
        Executes the automation using the specified automation player.
        Future enhancement: integrate dynamic scheduling adjustments based on system resource usage.
        """
        player_class = AUTOMATION_PLAYERS.get(task_type)
        if not player_class:
            log_error(f"Unsupported task type: {task_type}")
            return

        for loop in range(loop_count):
            loop_counter.value = loop + 1
            log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} using '{task_type}' automation.")
            player_instance = player_class()
            try:
                # Each loop plays one iteration of the video.
                player_instance.play_video(url, speed, 1)
            except Exception as e:
                log_error(f"Session {session_id} loop {loop + 1} encountered error: {e}")

        log_info(f"Session {session_id}: All {loop_count} loops completed.")
        if session_id in self.loop_counts:
            del self.loop_counts[session_id]

    def stop_session(self, session_id: str) -> bool:
        """
        Stops an active session and cleans up any running processes.
        :param session_id: The identifier of the session to stop.
        :return: True if the session was stopped, False otherwise.
        """
        if session_id in self.processes:
            process = self.processes[session_id]
            if isinstance(process, multiprocessing.Process):
                process.terminate()
                process.join()
                if session_id in self.loop_counts:
                    del self.loop_counts[session_id]
                log_info(f"Multiprocessing session {session_id} stopped.")
            else:
                process.revoke(terminate=True)
                log_info(f"Celery Task {session_id} revoked.")

            kill_browser_processes()
            del self.processes[session_id]
            return True
        return False

    def get_active_sessions(self) -> List[dict]:
        """
        Returns a list of active sessions along with their progress or status.
        :return: List of dictionaries, each representing a session.
        """
        active_sessions = []
        for session_id, proc in self.processes.items():
            if isinstance(proc, multiprocessing.Process):
                loop = self.loop_counts[session_id].value if session_id in self.loop_counts else 0
                active_sessions.append({"id": session_id, "loop": loop})
            else:
                active_sessions.append({"id": session_id, "status": getattr(proc, "status", "unknown")})
        return active_sessions


# Global Task Manager instance
task_manager = TaskManager()
