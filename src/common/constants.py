from pathlib import Path
import os

try:
    REL_PROJECT_ROOT = Path(__file__).parent.parent.parent
    ABS_PROJECT_ROOT = REL_PROJECT_ROOT.resolve()
except Exception:
    REL_PROJECT_ROOT = Path(os.getcwd())
    ABS_PROJECT_ROOT = REL_PROJECT_ROOT

LOGS_DIR = REL_PROJECT_ROOT / "log_folder" / "logs"

IMAGE_DESCRIBER_PROMPT_PATH = REL_PROJECT_ROOT / "src" / "prompts" / "image_describer.txt"

try:
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(IMAGE_DESCRIBER_PROMPT_PATH.parent, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")
