import multiprocessing
import os
from ytgrid.utils.logger import log_info
from ytgrid.automation.player import play_video

class TaskManager:
    """Manages concurrent video playback sessions using multiprocessing."""

    def __init__(self):
        self.processes = {}
        self.loop_counts = {}  # Replace multiprocessing.Manager() with standard dictionary

    def start_session(self, session_id, url, speed, loop_count):
        """Starts a new automation session in a separate process."""
        if session_id in self.processes:
            log_info(f"Session {session_id} already exists. Skipping duplicate.")
            return False  # Prevent duplicate sessions

        log_info(f"Starting session {session_id} for {url} with {loop_count} loops.")

        # Use multiprocessing.Value to track loops (safer than Manager.dict)
        loop_counter = multiprocessing.Value('i', 0)
        self.loop_counts[session_id] = loop_counter  

        process = multiprocessing.Process(target=self._start_process, args=(session_id, url, speed, loop_count, loop_counter))
        process.daemon = True  # Ensures cleanup on program exit
        process.start()

        self.processes[session_id] = process
        return True

    @staticmethod
    def _start_process(session_id, url, speed, loop_count, loop_counter):
        """Wrapper function for multiprocessing to avoid pickling issues."""
        os.environ["PYTHONWARNINGS"] = "ignore"
        task_manager.run_video(session_id, url, speed, loop_count, loop_counter)

    def run_video(self, session_id, url, speed, loop_count, loop_counter):
        """Runs video automation process and updates loop count."""
        for loop in range(loop_count):
            loop_counter.value = loop + 1  # Update loop progress
            log_info(f"Session {session_id}: Loop {loop + 1}/{loop_count} - Playing {url}")
            play_video(url, speed)
        log_info(f"Session {session_id}: All {loop_count} loops completed.")
        del self.loop_counts[session_id]  # Remove session after completion

    def stop_session(self, session_id):
        """Stops an active session by terminating its process."""
        if session_id in self.processes:
            self.processes[session_id].terminate()
            self.processes[session_id].join()
            del self.processes[session_id]
            if session_id in self.loop_counts:
                del self.loop_counts[session_id]
            log_info(f"Session {session_id} stopped.")
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
