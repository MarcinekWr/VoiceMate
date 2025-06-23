import json
import logging
import os
import tempfile
from datetime import datetime

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from opencensus.ext.azure.log_exporter import AzureLogHandler

load_dotenv()
logger = logging.getLogger(__name__)


def load_client() -> ElevenLabs:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("Brak ELEVENLABS_API_KEY w pliku .env")
        raise ValueError("Brak ELEVENLABS_API_KEY")

    return ElevenLabs(api_key=api_key)


def generate_audio_chunk(client: ElevenLabs, text: str, voice_id: str, model_id: str = "eleven_multilingual_v2") -> bytes:
    try:
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.3,
                "similarity_boost": 0.0,
                "style": 0.6,
                "use_speaker_boost": True
            }
        )
        return b"".join(audio)
    except Exception as e:
        logger.exception(f"Błąd podczas generowania audio dla voice_id '{voice_id}': {e}")
        raise


def generate_podcast_from_dialog(dialog_data: list = None, output_path: str = None, progress_callback=None) -> str:
    try:
        client = load_client()

        if not dialog_data:
            logger.error("Nie przekazano danych dialogowych.")
            return None

    except Exception:
        logger.error("Nie udało się przygotować klienta – przerwano generowanie.")
        return None

    logger.info(f"Załadowano {len(dialog_data)} wypowiedzi.")
    audio_chunks = []

    if output_path is None:
        temp_dir = tempfile.mkdtemp(prefix="podcast_")
        output_path = os.path.join(temp_dir, f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")

    total_segments = len(dialog_data)

    for i, part in enumerate(dialog_data):
        try:
            order = part.get("order")
            speaker = part.get("speaker")
            voice_id = part.get("voice_id")
            text = part.get("text")

            if order is None or not speaker or not voice_id or not text:
                logger.warning(f"Pominięto niepełny segment: {part}")
                continue

            logger.info(f"{order:02d}: {speaker} ({voice_id})")

            if progress_callback:
                progress_callback(i, total_segments, f"Generowanie segmentu {i+1}/{total_segments}: {speaker}")

            chunk = generate_audio_chunk(
                client=client,
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )
            audio_chunks.append(chunk)

        except Exception:
            logger.error(f"Nie udało się przetworzyć segmentu {part}")
            continue

    if not audio_chunks:
        logger.error("Nie wygenerowano żadnego segmentu – podcast nie został zapisany.")
        return None

    try:
        with open(output_path, "wb") as f:
            for chunk in audio_chunks:
                f.write(chunk)
        logger.info(f"Podcast zapisany jako {output_path}")
        return output_path
    except Exception as e:
        logger.exception(f"Błąd przy zapisie podcastu do pliku {output_path}: {e}")
        return None