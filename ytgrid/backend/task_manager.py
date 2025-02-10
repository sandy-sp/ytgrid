# ytgrid/backend/task_manager.py

import multiprocessing
import os
from ytgrid.utils.logger import log_info, log_error
from ytgrid.automation.player import VideoPlayer  # VideoPlayer implements AutomationPlayer

# Mapping from task type to automation player class.
AUTOMATION_PLAYERS = {
    "video": VideoPlayer,
    # Future: "batch": BatchPlayer, "channel": ChannelPlayer, etc.
}

class TaskManager:
    """Manages concurrent automation sessions using multiprocessing."""

    def __init__(self):
        self.processes = {}      # {session_id: Process}
        self.loop_counts = {}    # {session_id: multiprocessing.Value}

    def start_session(self, session_id, url, speed, loop_count, task_type="video"):
        """Starts a new automation session in a separate process."""
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False

        log_info(f"Starting session {session_id} for {url} with {loop_count} loops (task_type: {task_type}).")
        loop_counter = multiprocessing.Value('i', 0)
        self.loop_counts[session_id] = loop_counter

        process = multiprocessing.Process(
            target=self._start_process,
            args=(session_id, url, speed, loop_count, loop_counter, task_type)
        )
        process.daemon = True  # Cleanup on exit
        process.start()
        self.processes[session_id] = process
        return True

    @staticmethod
    def _start_process(session_id, url, speed, loop_count, loop_counter, task_type):
        """Wrapper for running automation in a separate process."""
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Call the global task_manager instance to run automation.
        task_manager.run_automation(session_id, url, speed, loop_count, loop_counter, task_type)

    def run_automation(self, session_id, url, speed, loop_count, loop_counter, task_type):
        """Runs the automation process using the selected automation player."""
        player_class = AUTOMATION_PLAYERS.get(task_type)
        if not player_class:
            log_error(f"Unsupported task type: {task_type}")
            return

        for loop in range(loop_count):
            loop_counter.value = loop + 1  # Update progress
            log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} with task '{task_type}'.")
            player_instance = player_class()  # Instantiate the concrete automation player
            # Each call plays one loop
            player_instance.play_video(url, speed, 1)
        log_info(f"Session {session_id}: All {loop_count} loops completed.")
        if session_id in self.loop_counts:
            del self.loop_counts[session_id]

    def stop_session(self, session_id):
        """Stops an active session by terminating its process and closing browsers."""
        if session_id in self.processes:
            self.processes[session_id].terminate()
            self.processes[session_id].join()
            del self.processes[session_id]
            if session_id in self.loop_counts:
                del self.loop_counts[session_id]
            log_info(f"Session {session_id} stopped.")
            # Kill any stray ChromeDriver and Chrome instances.
            os.system("pkill -f chromedriver")
            os.system("pkill -f chrome")
            return True
        return False

    def get_active_sessions(self):
        """Returns a list of active session IDs with their current loop progress."""
        return [
            {"id": session_id, "loop": self.loop_counts[session_id].value if session_id in self.loop_counts else 0}
            for session_id in self.processes.keys()
        ]

# Create a global task manager instance
task_manager = TaskManager()
