from __future__ import annotations

import os
import tempfile
import time
import wave

import azure.cognitiveservices.speech as speechsdk

from src.utils.key_vault import get_secret_env_first
from src.utils.logging_config import get_request_id, get_session_logger


class AzureTTSPodcastGenerator:
    """
    Podcast generator using Azure Cognitive Services Text-to-Speech.

    This class synthesizes speech from a list of dialog segments, each containing voice settings
    and text. The segments are saved as temporary WAV files, which are then merged into a final
    podcast audio file.

    :param request_id: Optional request identifier used for session-specific logging.
                       If not provided, a new ID will be generated automatically.
    """

    def __init__(self, request_id: str | None = None):
        self.request_id = request_id or get_request_id()
        self.logger = get_session_logger(self.request_id)
        api_key = get_secret_env_first("AZURE_SPEECH_API_KEY")
        region = "swedencentral"
        self.dir_prefix = "podcast_az_"

        if not api_key or not region:
            raise ValueError(
                "Missing AZURE_SPEECH_API_KEY or AZURE_SPEECH_REGION in .env",
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region,
        )

    def generate_podcast_azure(
        self,
        dialog_data: list,
        output_path: str | None = None,
        progress_callback=None,
    ) -> str | None:
        """
        Generate a podcast audio file from dialog data using Azure TTS.

        Each dialog segment is synthesized as a temporary WAV file and then all segments are combined
        into a single audio output file.

        :param dialog_data: List of dictionaries, each containing:
                            - 'text': the text to be synthesized
                            - 'voice_id': the Azure voice to use
                            - 'speaker': speaker name (for logs/UI)
                            - 'order': numeric order of the segment
        :param output_path: Optional path to save the final WAV file. If not provided, a temp file is created.
        :param progress_callback: Optional callback function called during processing with signature:
                                  (current_index, total_segments, message)
        :return: Path to the generated WAV file, or None if generation failed.
        """
        if not dialog_data:
            self.logger.error("No dialog data provided.")
            return None

        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix=self.dir_prefix)
            request_id = get_request_id()
            output_path = os.path.join(
                temp_dir,
                f"{self.dir_prefix}{request_id}.wav",
            )

        temp_files = []
        total_segments = len(dialog_data)

        for i, part in enumerate(dialog_data):
            voice = part.get("voice_id")
            text = part.get("text")
            order = part.get("order")

            if not voice or not text or order is None:
                self.logger.warning(f"Skipped incomplete segment: {part}")
                continue

            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_chunk_{order:02d}.wav",
                delete=False,
            )
            filename = temp_file.name
            temp_file.close()
            temp_files.append(filename)

            self.speech_config.speech_synthesis_voice_name = voice
            audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
            synthesizer = speechsdk.SpeechSynthesizer(
                self.speech_config,
                audio_config,
            )

            try:
                self.logger.info(f"{order:02d}: {part['speaker']} ({voice})")

                if progress_callback:
                    progress_callback(
                        i,
                        total_segments,
                        f"Generowanie segmentu {i+1}/{total_segments}: {part['speaker']}",
                    )

                result = synthesizer.speak_text_async(text).get()

                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.logger.error(f"Synthesis error for segment {order}")
                else:
                    self.logger.info(f"Segment {order:02d} generated")

            except Exception as e:
                self.logger.exception(
                    f"Exception while generating segment {order}: {e}",
                )
            finally:
                del synthesizer
                time.sleep(0.2)

        if progress_callback:
            progress_callback(
                total_segments,
                total_segments,
                "Łączenie segmentów...",
            )

        return self._combine_segments(temp_files, output_path)

    def _combine_segments(self, temp_files: list, output_path: str) -> str | None:
        """
        Combine multiple WAV segment files into a single output WAV file.

        Adds ~0.5 seconds of silence between each segment. After merging, temporary
        segment files are deleted.

        :param temp_files: List of paths to temporary WAV files.
        :param output_path: Final path where the merged audio file will be saved.
        :return: Path to the final output file, or None if merging failed.
        """
        self.logger.info("Merging WAV files...")

        first_file = next((f for f in temp_files if os.path.exists(f)), None)
        if not first_file:
            self.logger.error(
                "No files to merge - no segments were generated.",
            )
            return None

        try:
            with wave.open(first_file, "rb") as first_wave:
                params = first_wave.getparams()

                with wave.open(output_path, "wb") as output_wave:
                    output_wave.setparams(params)

                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            try:
                                with wave.open(temp_file, "rb") as temp_wave:
                                    output_wave.writeframes(
                                        temp_wave.readframes(
                                            temp_wave.getnframes(),
                                        ),
                                    )

                                silence_frames = int(params.framerate * 0.5)
                                silence_data = b"\x00" * (
                                    silence_frames * params.sampwidth * params.nchannels
                                )
                                output_wave.writeframes(silence_data)
                            except (wave.Error, OSError) as e:
                                self.logger.warning(
                                    f"Problem reading file {temp_file}: {e}",
                                )
                                return None

        except (wave.Error, OSError) as e:
            self.logger.exception(f"Error while merging WAV files: {e}")
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
                            self.logger.warning(
                                f"File {temp_file} locked, attempt {attempt + 1}/{max_retries}",
                            )
                            time.sleep(1)
                        else:
                            self.logger.warning(
                                f"Could not delete {temp_file} - please remove manually",
                            )
                    except Exception as e:
                        self.logger.error(
                            f"Error deleting file {temp_file}: {e}",
                        )
                        break

        self.logger.info(f"Podcast saved as {output_path}")
        return output_path
