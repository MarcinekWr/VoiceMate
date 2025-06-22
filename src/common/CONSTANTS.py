"""Constants for the project, including file paths and directories."""

from __future__ import annotations

import os
import logging
from pathlib import Path


REL_PROJECT_ROOT = Path(__file__).parent.parent.parent


ABS_PROJECT_ROOT = REL_PROJECT_ROOT.resolve()


LOG_FILE_PATH = ABS_PROJECT_ROOT / "log_folder" / "pdf_parser.log"

# Create log directory if it doesn't exist
os.makedirs(LOG_FILE_PATH.parent, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=str(LOG_FILE_PATH),
    filemode="w",
)
logger = logging.getLogger(__name__)

logging.info(f"Absolute project root set to: {ABS_PROJECT_ROOT}")


IMAGE_DESCRIBER_PROMPT_PATH = os.path.join(
    ABS_PROJECT_ROOT, "src", "prompts", "image_describer.txt"
)
