"""
Setup Script for YTGrid (Version 3)

This script ensures that the 'ytgrid' CLI script is accessible by adding the default pip --user
installation directory to the user's PATH if it isn't already present. It also verifies that
the 'ytgrid' CLI script is installed.
"""

import os
import sys
import shutil


def fix_path() -> None:
    """
    Ensures YTGrid is in the user's PATH after installation.

    It checks the default pip --user install location (usually ~/.local/bin) and adds it to the PATH
    if necessary. It then verifies that the 'ytgrid' CLI script is installed.
    """
    bin_path = os.path.expanduser("~/.local/bin")  # Default pip --user install location
    if bin_path not in os.environ.get("PATH", ""):
        print(f"📌 Adding {bin_path} to PATH (run 'export PATH=\"$HOME/.local/bin:$PATH\"' to make it permanent)")
        os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
    # Check if the 'ytgrid' CLI script is installed in the correct location.
    ytgrid_path = shutil.which("ytgrid")
    if ytgrid_path:
        print(f"✅ ytgrid installed at: {ytgrid_path}")
    else:
        print("❌ Error: ytgrid CLI script not found. Try running 'pip install --user ytgrid'.")


if __name__ == "__main__":
    fix_path()
