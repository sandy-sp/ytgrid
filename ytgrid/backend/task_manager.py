import multiprocessing
import os
from ytgrid.utils.logger import log_info, log_error
from ytgrid.automation.player import VideoPlayer  # Import your VideoPlayer (implements AutomationPlayer)

# Mapping from task type to automation player class.
AUTOMATION_PLAYERS = {
    "video": VideoPlayer,
    # In the future you could add: "batch": BatchPlayer, "channel": ChannelPlayer, etc.
}

class TaskManager:
    """Manages concurrent video playback sessions using multiprocessing."""

    def __init__(self):
        self.processes = {}      # {session_id: Process}
        self.loop_counts = {}    # {session_id: multiprocessing.Value}

    def start_session(self, session_id, url, speed, loop_count, task_type="video"):
        """Starts a new automation session in a separate process."""
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False  # Prevent duplicate sessions

        log_info(f"Starting session {session_id} for {url} with {loop_count} loops (task_type: {task_type}).")
        loop_counter = multiprocessing.Value('i', 0)
        self.loop_counts[session_id] = loop_counter

        process = multiprocessing.Process(
            target=self._start_process,
            args=(session_id, url, speed, loop_count, loop_counter, task_type)
        )
        process.daemon = True  # Ensures cleanup on program exit
        process.start()
        self.processes[session_id] = process
        return True

    @staticmethod
    def _start_process(session_id, url, speed, loop_count, loop_counter, task_type):
        """Wrapper function for multiprocessing to avoid pickling issues."""
        os.environ["PYTHONWARNINGS"] = "ignore"
        # Use the global task_manager instance to run the automation
        task_manager.run_automation(session_id, url, speed, loop_count, loop_counter, task_type)

    def run_automation(self, session_id, url, speed, loop_count, loop_counter, task_type):
        """Runs the automation process using the appropriate automation player and updates loop count."""
        player_class = AUTOMATION_PLAYERS.get(task_type)
        if not player_class:
            log_error(f"Unsupported task type: {task_type}")
            return

        for loop in range(loop_count):
            loop_counter.value = loop + 1  # Update loop progress
            log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url} using '{task_type}' automation.")
            player_instance = player_class()
            # We assume that each call to play_video plays one loop.
            player_instance.play_video(url, speed, 1)
        log_info(f"Session {session_id}: All {loop_count} loops completed.")
        if session_id in self.loop_counts:
            del self.loop_counts[session_id]

    def stop_session(self, session_id):
        """Stops an active session by terminating its process and closing browser instances."""
        if session_id in self.processes:
            self.processes[session_id].terminate()
            self.processes[session_id].join()
            del self.processes[session_id]
            if session_id in self.loop_counts:
                del self.loop_counts[session_id]
            log_info(f"Session {session_id} stopped.")
            # Ensure all browser instances are closed when a session stops
            os.system("pkill -f chromedriver")  # Kill any Chrome WebDriver instances
            os.system("pkill -f chrome")        # Kill any Chrome browsers
            return True
        return False

    def get_active_sessions(self):
        """Returns a list of active session IDs with loop progress."""
        return [
            {"id": session_id, "loop": self.loop_counts[session_id].value if session_id in self.loop_counts else 0}
            for session_id in self.processes.keys()
        ]

# Create a global task manager instance
task_manager = TaskManager()
