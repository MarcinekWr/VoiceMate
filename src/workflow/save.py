import logging
import os
import re

logger = logging.getLogger(__name__)


def dialog_to_json(raw_text: str, is_premium: bool = True) -> list:
    """Convert dialog text to JSON format"""
    speaker_map = {
        'P': 'o2xdfKUpc1Bwq7RchZuW',
        'S': 'CLuTGacrAhcIhaJslbXt',
    } if is_premium else {
        'P': 'pl-PL-MarekNeural',
        'S': 'pl-PL-ZofiaNeural'
    }

    pattern = re.compile(
        r'^\[(P|S)\]:\s*(.+?)(?=^\[P\]:|^\[S\]:|\Z)', re.MULTILINE | re.DOTALL)
    matches = pattern.findall(raw_text)

    if not matches:
        logger.warning('Nie znaleziono żadnych wypowiedzi w dialogu.')
        return []

    logger.info(f'Znaleziono {len(matches)} wypowiedzi w dialogu.')

    result = []
    for i, (role, text) in enumerate(matches, start=1):
        entry = {
            'order': i,
            'speaker': 'professor' if role == 'P' else 'student',
            'voice_id': speaker_map[role],
            'text': text.strip().replace('\n', ' ')
        }
        logger.debug(f'Wypowiedź {i}: {entry}')
        result.append(entry)

    return result


def save_to_file(content: str, filename: str, output_dir: str = 'output') -> str:
    """Save content to file and return the path"""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path
