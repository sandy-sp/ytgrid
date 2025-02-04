import subprocess
import time

# Start a session via CLI
print("Starting a session via CLI...")
subprocess.run(["ytgrid", "start", "--url", "https://www.youtube.com/watch?v=zU9y354XAgM", "--speed", "1.5", "--loops", "2"])

# Wait for 5 seconds before checking status
time.sleep(5)

# Check session status
print("\nChecking session status...")
subprocess.run(["ytgrid", "status"])

# Stop the session (Replace '1' with actual session ID if needed)
print("\nStopping the session...")
subprocess.run(["ytgrid", "stop", "--session_id", "1"])

print("\nSession stopped. Example CLI usage complete.")
