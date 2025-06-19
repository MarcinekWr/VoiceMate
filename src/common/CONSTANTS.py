"""Constants for the project, including file paths and directories."""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define log file path
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "log_folder", "pdf_parser.log")

# Create log directory if it doesn't exist
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Base directory: root of the project (2 levels up from CONSTANTS.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(f"Base directory set to: {BASE_DIR}")
