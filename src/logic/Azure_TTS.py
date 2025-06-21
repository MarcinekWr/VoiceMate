import logging
import os
import tempfile
import time
import wave
from datetime import datetime

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from opencensus.ext.azure.log_exporter import AzureLogHandler

load_dotenv()
logger = logging.getLogger(__name__)

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    connection_string = os.getenv("APPINSIGHTS_CONNECTION_STRING")
    if connection_string:
        azure_handler = AzureLogHandler(connection_string=connection_string)
        logger.addHandler(azure_handler)
        logger.info("AzureLogHandler podłączony – logi będą wysyłane do Application Insights")
    else:
        logger.warning("Brak APPINSIGHTS_CONNECTION_STRING – logi nie będą wysyłane do Application Insights")

def generate_podcast_simple_wav(dialog_data, output_path=None, progress_callback=None):  
    if output_path is None:
        temp_dir = tempfile.mkdtemp(prefix="podcast_")
        output_path = os.path.join(temp_dir, f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")

    temp_files = []
    total_segments = len(dialog_data)

    for i, part in enumerate(dialog_data):
        voice = part.get("voice_id")
        text = part.get("text")
        order = part.get("order")

        if not voice or not text or order is None:
            logger.warning(f"Pominięto niepełny segment: {part}")
            continue

        temp_file = tempfile.NamedTemporaryFile(suffix=f"_chunk_{order:02d}.wav", delete=False)
        filename = temp_file.name
        temp_file.close()
        temp_files.append(filename)

        synthesizer = None

        try:
            logger.info(f"{order:02d}: {part['speaker']} ({voice})")
            
            if progress_callback:
                progress_callback(i, total_segments, f"Generowanie segmentu {i+1}/{total_segments}: {part['speaker']}")

            speech_config = speechsdk.SpeechConfig(
                subscription=os.getenv("AZURE_SPEECH_API_KEY"),
                region=os.getenv("AZURE_SPEECH_REGION")
            )
            speech_config.speech_synthesis_voice_name = voice

            audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config, audio_config)

            result = synthesizer.speak_text_async(text).get()

            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.error(f"Błąd syntezy dla segmentu {order}")
            else:
                logger.info(f"Segment {order:02d} wygenerowany")

        except Exception as e:
            logger.exception(f"Wyjątek podczas generowania segmentu {order}: {e}")

        finally:
            if synthesizer:
                del synthesizer
            time.sleep(0.2)

    if progress_callback:
        progress_callback(total_segments, total_segments, "Łączenie segmentów...")

    logger.info("Łączenie plików WAV...")

    first_file = next((f for f in temp_files if os.path.exists(f)), None)
    if not first_file:
        logger.error("Brak plików do połączenia – nie wygenerowano żadnego segmentu.")
        return None

    try:
        with wave.open(first_file, 'rb') as first_wave:
            params = first_wave.getparams()

            with wave.open(output_path, 'wb') as output_wave:
                output_wave.setparams(params)

                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            with wave.open(temp_file, 'rb') as temp_wave:
                                output_wave.writeframes(temp_wave.readframes(temp_wave.getnframes()))

                            silence_frames = int(params.framerate * 0.5)
                            silence_data = b'\x00' * (silence_frames * params.sampwidth * params.nchannels)
                            output_wave.writeframes(silence_data)
                        except Exception as e:
                            logger.warning(f"Problem z odczytem pliku {temp_file}: {e}")

    except Exception as e:
        logger.exception(f"Błąd podczas łączenia plików WAV: {e}")
        return None

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    os.remove(temp_file)
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Plik {temp_file} zablokowany, próba {attempt + 1}/{max_retries}")
                        time.sleep(1)  
                    else:
                        logger.warning(f"Nie można usunąć {temp_file} – pozostaw ręcznie")
                except Exception as e:
                    logger.error(f"Błąd usuwania pliku {temp_file}: {e}")
                    break

    logger.info(f"Podcast zapisany jako {output_path}")
    return output_path


