import json
import re


def dialog_to_json(raw_text: str, is_premium: bool = True) -> list:
    speaker_map = {
        "P": "o2xdfKUpc1Bwq7RchZuW", 
        "S": "CLuTGacrAhcIhaJslbXt",  
    } if is_premium else {
        "P": "pl-PL-MarekNeural",
        "S": "pl-PL-ZofiaNeural"
    }

    pattern = re.compile(r"^\[(P|S)\]:\s*(.+?)(?=^\[P\]:|^\[S\]:|\Z)", re.MULTILINE | re.DOTALL)
    matches = pattern.findall(raw_text)
    
    result = []
    for i, (role, text) in enumerate(matches, start=1):
        result.append({
            "order": i,
            "speaker": "professor" if role == "P" else "student",
            "voice_id": speaker_map[role],
            "text": text.strip().replace("\n", " ")
        })
    return result


if __name__ == "__main__":
    is_premium = False

    with open("src/logic/podcast_output.txt", "r", encoding="utf-8") as f:
        raw_dialog = f.read()
        json_data = dialog_to_json(raw_dialog, is_premium=is_premium)

    with open("podcast_output_free.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)