import os
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

from src.logic.Elevenlabs_TTS import ElevenlabsTTSPodcastGenerator


class TestElevenlabsTTSPodcastGenerator(unittest.TestCase):
    def setUp(self):
        self.api_key = 'test_key'
        self.env_patcher = patch.dict(
            os.environ,
            {'ELEVENLABS_API_KEY': self.api_key},
        )
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('src.logic.Elevenlabs_TTS.ElevenLabs')
    def test_init_success(self, mock_client):
        generator = ElevenlabsTTSPodcastGenerator()
        self.assertIsNotNone(generator.client)

    def test_init_missing_api_key(self):
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}, clear=True):
            with self.assertRaises(ValueError):
                ElevenlabsTTSPodcastGenerator()

    @patch('src.logic.Elevenlabs_TTS.ElevenLabs')
    def test_generate_audio_chunk_success(self, mock_client):
        generator = ElevenlabsTTSPodcastGenerator()
        mock_response = [b'audio1', b'audio2']
        mock_client.return_value.text_to_speech.convert.return_value = (
            mock_response
        )

        result = generator.generate_audio_chunk('test', 'voice123')
        self.assertEqual(result, b'audio1audio2')

    @patch('src.logic.Elevenlabs_TTS.ElevenLabs')
    def test_generate_audio_chunk_exception(self, mock_client):
        generator = ElevenlabsTTSPodcastGenerator()
        mock_client.return_value.text_to_speech.convert.side_effect = (
            Exception(
                'conversion error',
            )
        )

        with self.assertRaises(Exception):
            generator.generate_audio_chunk('test', 'voice123')

    @patch('src.logic.Elevenlabs_TTS.get_request_id', return_value='abc123')
    def test_generate_podcast_empty_dialog_data(self, mock_rid):
        generator = ElevenlabsTTSPodcastGenerator()
        result = generator.generate_podcast_elevenlabs(
            [],
        )  # 👈 poprawiona metoda
        self.assertIsNone(result)

    @patch('src.logic.Elevenlabs_TTS.get_request_id', return_value='abc123')
    @patch('builtins.open', new_callable=mock_open)
    @patch('tempfile.mkdtemp', return_value='/tmp/testpodcast')
    @patch.object(
        ElevenlabsTTSPodcastGenerator,
        'generate_audio_chunk',
        return_value=b'abc',
    )
    def test_generate_podcast_success(
        self,
        mock_chunk,
        mock_tmp,
        mock_open_file,
        mock_rid,
    ):
        generator = ElevenlabsTTSPodcastGenerator()
        dialog = [
            {'voice_id': 'id1', 'text': 'hello', 'order': 1, 'speaker': 'A'},
            {'voice_id': 'id2', 'text': 'world', 'order': 2, 'speaker': 'B'},
        ]

        result = generator.generate_podcast_elevenlabs(dialog)

        expected_path = os.path.normpath(
            os.path.join(
                '/tmp/testpodcast',
                'podcast_abc123.wav',
            ),
        )

        self.assertEqual(os.path.normpath(result), expected_path)

        mock_open_file.assert_called_once()
        call_args = mock_open_file.call_args
        opened_path, mode = call_args[0]

        self.assertEqual(os.path.normpath(opened_path), expected_path)
        self.assertEqual(mode, 'wb')

        handle = mock_open_file()
        handle.write.assert_any_call(b'abc')

    @patch('src.logic.Elevenlabs_TTS.get_request_id', return_value='abc123')
    @patch.object(ElevenlabsTTSPodcastGenerator, 'generate_audio_chunk')
    def test_generate_podcast_skips_incomplete_segments(
        self,
        mock_chunk,
        mock_rid,
    ):
        generator = ElevenlabsTTSPodcastGenerator()
        dialog = [
            {'voice_id': '', 'text': 'missing', 'order': 1, 'speaker': 'A'},
            {'voice_id': 'id', 'text': '', 'order': 2, 'speaker': 'B'},
            {'voice_id': 'id', 'text': 'ok', 'order': 3, 'speaker': 'C'},
        ]
        mock_chunk.return_value = b'valid'

        with patch('builtins.open', mock_open()) as m, patch(
            'tempfile.mkdtemp',
            return_value='/tmp/testpodcast',
        ):
            result = generator.generate_podcast_elevenlabs(dialog)
            self.assertIn('podcast_abc123.wav', result)
            self.assertEqual(mock_chunk.call_count, 1)

    @patch('src.logic.Elevenlabs_TTS.get_request_id', return_value='abc123')
    @patch('tempfile.mkdtemp', return_value='/tmp/testpodcast')
    @patch.object(
        ElevenlabsTTSPodcastGenerator,
        'generate_audio_chunk',
        return_value=b'abc',
    )
    @patch('builtins.open', side_effect=Exception('write error'))
    def test_generate_podcast_write_error(
        self,
        mock_open_file,
        mock_chunk,
        mock_tmp,
        mock_rid,
    ):
        generator = ElevenlabsTTSPodcastGenerator()
        dialog = [
            {'voice_id': 'id', 'text': 'test', 'order': 1, 'speaker': 'A'},
        ]

        result = generator.generate_podcast_elevenlabs(dialog)
        self.assertIsNone(result)

    @patch('src.logic.Elevenlabs_TTS.get_request_id', return_value='abc123')
    @patch('tempfile.mkdtemp', return_value='/tmp/testpodcast')
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(
        ElevenlabsTTSPodcastGenerator,
        'generate_audio_chunk',
        return_value=b'chunk',
    )
    def test_generate_podcast_progress_callback(
        self,
        mock_chunk,
        mock_open_file,
        mock_tmp,
        mock_rid,
    ):
        generator = ElevenlabsTTSPodcastGenerator()
        dialog = [
            {'voice_id': 'id', 'text': 'test', 'order': 1, 'speaker': 'A'},
        ]
        callback = MagicMock()

        generator.generate_podcast_elevenlabs(
            dialog,
            progress_callback=callback,
        )

        callback.assert_has_calls(
            [
                call(0, 1, 'Generowanie segmentu 1/1: A'),
            ],
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
