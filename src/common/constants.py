from pathlib import Path
import os

REL_PROJECT_ROOT = Path(__file__).parent.parent.parent
ABS_PROJECT_ROOT = REL_PROJECT_ROOT.resolve()

LOGS_DIR = REL_PROJECT_ROOT / "log_folder" / "logs"
IMAGE_DESCRIBER_PROMPT_PATH = (
    REL_PROJECT_ROOT / "src" / "prompts" / "image_describer.txt"
)

try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DESCRIBER_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create directories: {e}")
