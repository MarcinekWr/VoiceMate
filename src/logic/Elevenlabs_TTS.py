from __future__ import annotations

import logging
import os
import tempfile

from elevenlabs.client import ElevenLabs

from src.utils.logging_config import get_request_id


class ElevenlabsTTSPodcastGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = self._load_client()
        self.dir_prefix = 'podcast_el_'

    def _load_client(self) -> ElevenLabs:
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            self.logger.error('Missing ELEVENLABS_API_KEY in file .env')
            raise ValueError('Missing ELEVENLABS_API_KEY')
        return ElevenLabs(api_key=api_key)

    def generate_audio_chunk(
        self, text: str, voice_id: str, model_id: str = 'eleven_multilingual_v2',
    ) -> bytes:
        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format='mp3_44100_128',
                voice_settings={
                    'stability': 0.3,
                    'similarity_boost': 0.0,
                    'style': 0.6,
                    'use_speaker_boost': True,
                },
            )
            return b''.join(audio)
        except Exception as e:
            self.logger.exception(
                f"Error while generating audio for voice_id '{voice_id}': {e}",
            )
            raise

    def generate_podcast_elevenlabs(
        self, dialog_data: list, output_path: str = None, progress_callback=None,
    ) -> str:
        if not dialog_data:
            self.logger.error('No dialog data provided.')
            return None

        self.logger.info(f'Loaded {len(dialog_data)} utterances.')
        audio_chunks = []

        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix=self.dir_prefix)
            request_id = get_request_id()
            output_path = os.path.join(
                temp_dir, f'{self.dir_prefix}{request_id}.wav',
            )

        total_segments = len(dialog_data)

        for i, part in enumerate(dialog_data):
            try:
                order = part.get('order')
                speaker = part.get('speaker')
                voice_id = part.get('voice_id')
                text = part.get('text')

                if order is None or not speaker or not voice_id or not text:
                    self.logger.warning(f'Skipped incomplete segment: {part}')
                    continue

                self.logger.info(f'{order:02d}: {speaker} ({voice_id})')

                if progress_callback:
                    progress_callback(
                        i,
                        total_segments,
                        f'Generowanie segmentu {i+1}/{total_segments}: {speaker}',
                    )

                chunk = self.generate_audio_chunk(text=text, voice_id=voice_id)
                audio_chunks.append(chunk)

            except Exception:
                self.logger.error(f'Failed to process segment {part}')
                continue

        if not audio_chunks:
            self.logger.error('No segments generated – podcast was not saved.')
            return None

        try:
            with open(output_path, 'wb') as f:
                for chunk in audio_chunks:
                    f.write(chunk)
            self.logger.info(f'Podcast saved as {output_path}')
            return output_path
        except Exception as e:
            self.logger.exception(
                f'Error saving podcast to file {output_path}: {e}',
            )
            return None
