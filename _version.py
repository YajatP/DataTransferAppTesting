# Auto-generated version info — updated by CI or git
# Do not edit manually; use `python _version.py` to regenerate from git tags

import subprocess
import os

APP_VERSION = "dev"
BUILD_DATE = "unknown"

def _get_git_version():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__)) or "."
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "dev"

def _get_build_date():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

def get_version():
    """Get the app version, preferring the baked-in value over git."""
    if APP_VERSION != "dev":
        return APP_VERSION
    return _get_git_version()

def get_build_date():
    """Get the build date, preferring the baked-in value."""
    if BUILD_DATE != "unknown":
        return BUILD_DATE
    return _get_build_date()

if __name__ == "__main__":
    # When run directly, print version info (useful for CI)
    v = _get_git_version()
    d = _get_build_date()
    print(f"Version: {v}")
    print(f"Build Date: {d}")
    # Rewrite this file with baked-in values
    here = os.path.abspath(__file__)
    with open(here, "r") as f:
        content = f.read()
    content = content.replace('APP_VERSION = "dev"', f'APP_VERSION = "{v}"')
    content = content.replace('BUILD_DATE = "unknown"', f'BUILD_DATE = "{d}"')
    with open(here, "w") as f:
        f.write(content)
    print(f"Baked version {v} into {here}")
