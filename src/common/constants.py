import os

REL_PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..'))
LOGS_DIR = os.path.join(REL_PROJECT_ROOT, 'log_folder', 'logs')
IMAGE_DESCRIBER_PROMPT_PATH = os.path.join(
    REL_PROJECT_ROOT, 'src', 'prompts', 'image_describer.txt')

try:
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(IMAGE_DESCRIBER_PROMPT_PATH), exist_ok=True)
except OSError as e:
    print(f'Warning: Could not create directories: {e}')
