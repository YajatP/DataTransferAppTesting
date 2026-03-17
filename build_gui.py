#!/usr/bin/env python3
"""
Build script — packages scout_transfer_gui.py into a standalone app.

Usage:
    pip install pyinstaller
    python build_gui.py

Output:
    macOS → dist/ScoutTransfer.app
    Windows → dist/ScoutTransfer.exe
"""

import subprocess
import sys
import os

APP_NAME = "ScoutTransfer"
MAIN_SCRIPT = "scout_transfer_gui.py"
ICON_PATH = os.path.join("icons", "mercs.png")

def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        # Bundle scout_transfer.py alongside the GUI
        "--add-data", f"scout_transfer.py{os.pathsep}.",
        # Bundle the icon
        "--add-data", f"icons{os.pathsep}icons",
    ]

    # Use icon if available (macOS .icns or .png, Windows .ico)
    if os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])

    cmd.append(MAIN_SCRIPT)

    print(f"Building {APP_NAME}...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) or ".")
    if result.returncode == 0:
        print(f"\n✓ Build complete! Check the 'dist/' folder for {APP_NAME}.")
    else:
        print(f"\n✗ Build failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
