import multiprocessing
import os
import signal
import threading
from typing import Dict, List, Optional

from multiprocessing.sharedctypes import Synchronized

from ytgrid.utils.logger import log_info, log_error
from ytgrid.automation.player import VideoPlayer
from ytgrid.automation.playlist_player import PlaylistPlayer
from ytgrid.automation.channel_player import ChannelPlayer
from ytgrid.utils.config import config

# Mapping from task type to automation player class.
AUTOMATION_PLAYERS: Dict[str, object] = {
    "video": VideoPlayer,
    "playlist": PlaylistPlayer,
    "channel": ChannelPlayer,
}

from ytgrid.optimizer.orchestrator import optimizer


def _record_execution_end(
    session_id: str, status: str, error_message: Optional[str] = None
) -> None:
    """Persist an execution outcome. Best-effort — never breaks automation.

    Runs inside the worker process where no event loop exists, so asyncio.run()
    is the correct entry point. A no-op if no matching history row exists.
    """
    try:
        import asyncio
        from ytgrid.database.repository import ProfileRepository

        async def _record() -> None:
            await ProfileRepository().record_execution_end(session_id, status, error_message)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_record())
        else:
            errors: list[BaseException] = []

            def _run_in_thread() -> None:
                try:
                    asyncio.run(_record())
                except BaseException as exc:
                    errors.append(exc)

            thread = threading.Thread(target=_run_in_thread)
            thread.start()
            thread.join()
            if errors:
                raise errors[0]
    except Exception as e:
        log_error(f"Failed to record execution end for {session_id}: {e}")


class TaskManager:
    """
    Manages automation sessions using either multiprocessing or Celery.
    Future enhancements include dynamic scheduling based on system resource usage.
    """
    def __init__(self) -> None:
        self.processes: Dict[str, object] = {}  # {session_id: Process or Celery Task}
        self.loop_counts: Dict[str, Synchronized] = {}  # {session_id: shared synchronized value}
        self.last_start_error: Optional[str] = None
        self._lock = threading.RLock()

    def start_session(
        self,
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        task_type: str = "video",
        use_celery: Optional[bool] = None
    ) -> bool:
        """
        Starts an automation session.

        :param session_id: Unique identifier for the session.
        :param url: URL of the video to be played.
        :param speed: Playback speed.
        :param loop_count: Total number of loops to run.
        :param task_type: Type of automation task (default "video").
        :param use_celery: Optional flag to override default Celery setting.
        :return: True if the session is started successfully, False otherwise.
        """
        self.last_start_error = None

        if task_type not in AUTOMATION_PLAYERS:
            self.last_start_error = f"Unsupported task type: {task_type}"
            log_error(self.last_start_error)
            return False

        if optimizer.is_throttled:
            self.last_start_error = "System resources under pressure"
            log_error(f"Session {session_id} rejected: {self.last_start_error}.")
            return False

        if session_id in self.processes:
            self.last_start_error = "Session already exists"
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

    def _prune_finished_processes(self) -> None:
        """
        Remove finished local/Celery tasks from the active-session registry.

        Child processes cannot mutate the parent TaskManager, so pruning must
        happen from parent-side reads such as status and dashboard polling.
        """
        with self._lock:
            for session_id, proc in list(self.processes.items()):
                if isinstance(proc, multiprocessing.Process):
                    if proc.is_alive():
                        continue
                    proc.join(timeout=0)
                    self.loop_counts.pop(session_id, None)
                    del self.processes[session_id]
                elif getattr(proc, "ready", lambda: False)():
                    del self.processes[session_id]

    @staticmethod
    def _start_process(
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        loop_counter: Synchronized,
        task_type: str
    ) -> None:
        """
        Static helper to run automation in a separate process.
        """
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Start a new session/process group so every browser child spawned by this
        # automation run can be terminated together via os.killpg() on stop.
        try:
            os.setsid()
        except OSError:
            pass
        # Invokes the global task_manager's run_automation method.
        task_manager.run_automation(session_id, url, speed, loop_count, loop_counter, task_type)

    def run_automation(
        self,
        session_id: str,
        url: str,
        speed: float,
        loop_count: int,
        loop_counter: Synchronized,
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

        player_instance = player_class()
        try:
            for loop in range(loop_count):
                loop_counter.value = loop + 1
                log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} using '{task_type}' automation.")
                # Each loop plays one iteration of the video.
                player_instance.play_video(url, speed, 1)
        except Exception as e:
            log_error(f"Session {session_id} encountered error: {e}")
            _record_execution_end(session_id, "failed", str(e))
            raise

        _record_execution_end(session_id, "completed")
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
                # Capture the process group before terminating so the whole tree
                # (the worker plus its chromedriver/chrome children) can be reaped.
                pgid = None
                if process.pid:
                    try:
                        pgid = os.getpgid(process.pid)
                    except (ProcessLookupError, PermissionError):
                        pgid = None

                process.terminate()
                process.join(timeout=10)
                if process.is_alive():
                    log_error(f"Multiprocessing session {session_id} did not terminate cleanly. Sending SIGKILL.")
                    try:
                        os.kill(process.pid, signal.SIGKILL)
                    except (ProcessLookupError, TypeError):
                        pass  # Process already exited

                # Kill the whole process group to clean up browser children.
                if pgid is not None and pgid != os.getpgrp():
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass

                if session_id in self.loop_counts:
                    del self.loop_counts[session_id]
                log_info(f"Multiprocessing session {session_id} stopped.")
            else:
                process.revoke(terminate=True)
                log_info(f"Celery Task {session_id} revoked.")

            _record_execution_end(session_id, "stopped")
            del self.processes[session_id]
            return True
        return False

    def get_active_sessions(self) -> List[dict]:
        """
        Returns a list of active sessions along with their progress or status.

        :return: List of dictionaries, each representing a session.
        """
        self._prune_finished_processes()
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
