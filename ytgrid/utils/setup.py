import os
import sys
import shutil

def fix_path():
    """Ensures ytgrid is in the user's $PATH after installation."""
    bin_path = os.path.expanduser("~/.local/bin")  # Default pip --user install location
    if bin_path not in os.environ["PATH"]:
        print(f"📌 Adding {bin_path} to PATH (run 'export PATH=\"$HOME/.local/bin:$PATH\"' to make it permanent)")
        os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"
    
    # Check if ytgrid is installed in the correct location
    ytgrid_path = shutil.which("ytgrid")
    if ytgrid_path:
        print(f"✅ ytgrid installed at: {ytgrid_path}")
    else:
        print("❌ Error: ytgrid CLI script not found. Try running 'pip install --user ytgrid'.")

if __name__ == "__main__":
    fix_path()
