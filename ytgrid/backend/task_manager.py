import multiprocessing
import os
from ytgrid.utils.logger import log_info
from ytgrid.automation.player import play_video

class TaskManager:
    """Manages concurrent video playback sessions using multiprocessing."""

    def __init__(self):
        self.processes = {}

    def start_session(self, session_id, url, speed, loop_count):
        """Starts a new automation session in a separate process."""
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False  # Prevent duplicate sessions
        
        log_info(f"Starting session {session_id} for {url} with {loop_count} loops.")

        # Use a wrapper function to prevent pickling issues
        process = multiprocessing.Process(target=self.run_video, args=(session_id, url, speed, loop_count))
        process.daemon = True  # Ensure it doesn't keep running if the main process is killed
        process.start()

        self.processes[session_id] = process
        return True

    @staticmethod
    def run_video(session_id, url, speed, loop_count):
        """Standalone function to play videos (works with multiprocessing)."""
        os.environ["PYTHONWARNINGS"] = "ignore"  # Avoid multiprocessing warnings
        for loop in range(loop_count):
            print(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url}")
            play_video(url, speed)
        print(f"Session {session_id}: All {loop_count} loops completed.")

    def stop_session(self, session_id):
        """Stops an active session by terminating its process."""
        if session_id in self.processes:
            self.processes[session_id].terminate()
            self.processes[session_id].join()
            del self.processes[session_id]
            log_info(f"Session {session_id} stopped.")
            return True
        return False

    def get_active_sessions(self):
        """Returns a list of active session IDs."""
        return list(self.processes.keys())

# Create a global task manager instance
task_manager = TaskManager()
