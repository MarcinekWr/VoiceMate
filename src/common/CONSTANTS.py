"""Constants for the project, including file paths and directories."""
from pathlib import Path

# Base directory: root of the project (2 levels up from CONSTANTS.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(f"Base directory set to: {BASE_DIR}")
# Log file path
LOG_FILE_PATH = BASE_DIR / "log_folder" / "log_files.log"
# Ensure the log folder exists
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)