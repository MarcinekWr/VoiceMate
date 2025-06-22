"""Constants for the project, including file paths and directories."""

from __future__ import annotations

import os
from pathlib import Path

# Path resolution
try:
    REL_PROJECT_ROOT = Path(__file__).parent.parent.parent
    ABS_PROJECT_ROOT = REL_PROJECT_ROOT.resolve()
except Exception:
    # Fallback for cases where __file__ might not work (e.g., some test environments)
    REL_PROJECT_ROOT = Path(os.getcwd())
    ABS_PROJECT_ROOT = REL_PROJECT_ROOT

# File paths
LOG_FILE_PATH = REL_PROJECT_ROOT / "log_folder" / "pdf_parser.log"
IMAGE_DESCRIBER_PROMPT_PATH = (
    REL_PROJECT_ROOT / "src" / "prompts" / "image_describer.txt"
)

# Ensure directories exist
try:
    os.makedirs(LOG_FILE_PATH.parent, exist_ok=True)
    if not IMAGE_DESCRIBER_PROMPT_PATH.parent.exists():
        os.makedirs(IMAGE_DESCRIBER_PROMPT_PATH.parent, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")
