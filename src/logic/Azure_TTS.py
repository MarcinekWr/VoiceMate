from __future__ import annotations

import logging
import os
import tempfile
import time
import wave
from typing import Optional

import azure.cognitiveservices.speech as speechsdk

from src.utils.logging_config import get_request_id


class AzureTTSPodcastGenerator:
    def __init__(self):
        api_key = os.getenv('AZURE_SPEECH_API_KEY')
        region = os.getenv('AZURE_SPEECH_REGION')
        self.logger = logging.getLogger(__name__)
        self.dir_prefix = 'podcast_az_'

        if not api_key or not region:
            raise ValueError(
                'Missing AZURE_SPEECH_API_KEY or AZURE_SPEECH_REGION in .env',
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key, region=region,
        )

    def generate_podcast_azure(
        self, dialog_data: list, output_path: str = None, progress_callback=None,
    ) -> str:
        if not dialog_data:
            self.logger.error('No dialog data provided.')
            return None

        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix=self.dir_prefix)
            request_id = get_request_id()
            output_path = os.path.join(
                temp_dir, f'{self.dir_prefix}{request_id}.wav',
            )

        temp_files = []
        total_segments = len(dialog_data)

        for i, part in enumerate(dialog_data):
            voice = part.get('voice_id')
            text = part.get('text')
            order = part.get('order')

            if not voice or not text or order is None:
                self.logger.warning(f'Skipped incomplete segment: {part}')
                continue

            temp_file = tempfile.NamedTemporaryFile(
                suffix=f'_chunk_{order:02d}.wav', delete=False,
            )
            filename = temp_file.name
            temp_file.close()
            temp_files.append(filename)

            self.speech_config.speech_synthesis_voice_name = voice
            audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
            synthesizer = speechsdk.SpeechSynthesizer(
                self.speech_config, audio_config,
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
                    self.logger.error(f'Synthesis error for segment {order}')
                else:
                    self.logger.info(f'Segment {order:02d} generated')

            except Exception as e:
                self.logger.exception(
                    f'Exception while generating segment {order}: {e}',
                )
            finally:
                del synthesizer
                time.sleep(0.2)

        if progress_callback:
            progress_callback(
                total_segments, total_segments,
                'Łączenie segmentów...',
            )

        return self._combine_segments(temp_files, output_path)

    def _combine_segments(self, temp_files: list, output_path: str) -> str:
        self.logger.info('Merging WAV files...')

        first_file = next((f for f in temp_files if os.path.exists(f)), None)
        if not first_file:
            self.logger.error(
                'No files to merge - no segments were generated.',
            )
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
                                    output_wave.writeframes(
                                        temp_wave.readframes(
                                            temp_wave.getnframes(),
                                        ),
                                    )

                                silence_frames = int(params.framerate * 0.5)
                                silence_data = b'\x00' * (
                                    silence_frames * params.sampwidth * params.nchannels
                                )
                                output_wave.writeframes(silence_data)
                            except (wave.Error, OSError) as e:
                                self.logger.warning(
                                    f'Problem reading file {temp_file}: {e}',
                                )
                                return None

        except (wave.Error, OSError) as e:
            self.logger.exception(f'Error while merging WAV files: {e}')
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
                                f'File {temp_file} locked, attempt {attempt + 1}/{max_retries}',
                            )
                            time.sleep(1)
                        else:
                            self.logger.warning(
                                f'Could not delete {temp_file} - please remove manually',
                            )
                    except Exception as e:
                        self.logger.error(
                            f'Error deleting file {temp_file}: {e}',
                        )
                        break

        self.logger.info(f'Podcast saved as {output_path}')
        return output_path
