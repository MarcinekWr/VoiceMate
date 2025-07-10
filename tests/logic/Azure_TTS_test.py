from __future__ import annotations

import logging
import os
import unittest
from unittest.mock import MagicMock, Mock, call, patch

import azure.cognitiveservices.speech as speechsdk

from src.logic.Azure_TTS import AzureTTSPodcastGenerator


class TestAzureTTSPodcastGenerator(unittest.TestCase):
    """Kompleksowe testy dla klasy AzureTTSPodcastGenerator"""

    def setUp(self):
        """Przygotowanie środowiska testowego"""
        self.api_key = 'test_api_key'
        self.region = 'test_region'

        # Mock zmiennych środowiskowych
        self.env_patcher = patch.dict(
            os.environ,
            {
                'AZURE_SPEECH_API_KEY': self.api_key,
                'AZURE_SPEECH_REGION': self.region,
            },
        )
        self.env_patcher.start()

        # Mock speechsdk.SpeechConfig
        self.speech_config_mock = Mock()
        self.speech_config_patcher = patch(
            'azure.cognitiveservices.speech.SpeechConfig',
            return_value=self.speech_config_mock,
        )
        self.speech_config_patcher.start()

    def tearDown(self):
        """Czyszczenie po testach"""
        self.env_patcher.stop()
        self.speech_config_patcher.stop()

    def test_init_success(self):
        """Test pomyślnej inicjalizacji"""
        generator = AzureTTSPodcastGenerator()

        self.assertIsNotNone(generator.speech_config)
        self.assertIsInstance(generator.logger, logging.Logger)

    @patch('src.logic.Azure_TTS.get_secret_env_first', side_effect=ValueError('Brakuje AZURE_SPEECH_API_KEY'))
    def test_init_missing_api_key(self, mock_get_secret):
        """Test inicjalizacji bez klucza API (symulowana sytuacja braku)"""
        with self.assertRaises(ValueError) as context:
            AzureTTSPodcastGenerator()

        self.assertIn('Brakuje AZURE_SPEECH_API_KEY', str(context.exception))

        @patch('src.logic.Azure_TTS.get_secret_env_first', side_effect=[
            'test_api_key',
            ValueError('Brakuje AZURE_SPEECH_REGION')
        ])
        def test_init_missing_region(self, mock_get_secret):
            """Test inicjalizacji bez regionu"""
            with self.assertRaises(ValueError) as context:
                AzureTTSPodcastGenerator()

            self.assertIn('Brakuje AZURE_SPEECH_REGION',
                          str(context.exception))

        @patch('src.logic.Azure_TTS.get_secret_env_first', side_effect=[
            ValueError('Brakuje AZURE_SPEECH_API_KEY'),
            ValueError('AZURE_SPEECH_REGION missing')
        ])
        def test_init_missing_both_credentials(self, mock_get_secret):
            """Test inicjalizacji bez obu wymaganych zmiennych"""
            with self.assertRaises(ValueError) as context:
                AzureTTSPodcastGenerator()

            self.assertIn('Brakuje AZURE_SPEECH_API_KEY',
                          str(context.exception))

    @patch(
        'src.utils.logging_config.get_request_id',
        return_value='test_request_123',
    )
    @patch('tempfile.mkdtemp', return_value='/tmp/podcast_test')
    def test_generate_podcast_empty_dialog_data(
        self, mock_mkdtemp, mock_get_request_id,
    ):
        """Test generowania podcastu z pustymi danymi"""
        generator = AzureTTSPodcastGenerator()

        with patch.object(generator.logger, 'error') as mock_logger_error:
            result = generator.generate_podcast_azure([])

            mock_logger_error.assert_called_once_with(
                'No dialog data provided.',
            )
            self.assertIsNone(result)

    @patch(
        'src.utils.logging_config.get_request_id',
        return_value='test_request_123',
    )
    @patch('tempfile.mkdtemp', return_value='/tmp/podcast_test')
    @patch('tempfile.NamedTemporaryFile')
    @patch('azure.cognitiveservices.speech.audio.AudioOutputConfig')
    @patch('azure.cognitiveservices.speech.SpeechSynthesizer')
    @patch(
        'os.path.join', return_value='/tmp/podcast_test/podcast_test_request_123.wav',
    )
    def test_generate_podcast_success(
        self,
        mock_join,
        mock_synthesizer_class,
        mock_audio_config,
        mock_temp_file,
        mock_mkdtemp,
        mock_get_request_id,
    ):
        """Test pomyślnego generowania podcastu"""
        generator = AzureTTSPodcastGenerator()

        # Przygotowanie danych testowych
        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Witamy w naszym podcaście',
                'order': 1,
                'speaker': 'Marek',
            },
            {
                'voice_id': 'pl-PL-ZofiaNeural',
                'text': 'Dzisiaj porozmawiamy o testowaniu',
                'order': 2,
                'speaker': 'Zofia',
            },
        ]

        # Mock temp file
        mock_temp_file_instance = Mock()
        mock_temp_file_instance.name = '/tmp/temp_chunk_01.wav'
        mock_temp_file.return_value = mock_temp_file_instance

        # Mock synthesizer
        mock_synthesizer = Mock()
        mock_result = Mock()
        mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
        mock_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_result
        )
        mock_synthesizer_class.return_value = mock_synthesizer

        # Mock combine_segments
        expected_output = '/tmp/podcast_test/podcast_test_request_123.wav'
        with patch.object(
            generator, '_combine_segments', return_value=expected_output,
        ) as mock_combine:
            result = generator.generate_podcast_azure(dialog_data)

            self.assertEqual(result, expected_output)
            mock_combine.assert_called_once()

    @patch('tempfile.NamedTemporaryFile')
    @patch('azure.cognitiveservices.speech.audio.AudioOutputConfig')
    @patch('azure.cognitiveservices.speech.SpeechSynthesizer')
    def test_generate_podcast_incomplete_segment(
        self, mock_synthesizer_class, mock_audio_config, mock_temp_file,
    ):
        """Test obsługi niepełnych segmentów"""
        generator = AzureTTSPodcastGenerator()

        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Kompletny segment',
                'order': 1,
                'speaker': 'Marek',
            },
            {
                'voice_id': '',  # Brakujący voice_id
                'text': 'Niepełny segment',
                'order': 2,
                'speaker': 'Zofia',
            },
            {
                'voice_id': 'pl-PL-ZofiaNeural',
                # Brakujący text
                'order': 3,
                'speaker': 'Zofia',
            },
        ]

        with patch.object(generator.logger, 'warning') as mock_logger_warning:
            with patch.object(
                generator, '_combine_segments', return_value='output.wav',
            ):
                result = generator.generate_podcast_azure(dialog_data)

                # Sprawdź czy niepełne segmenty zostały pominięte
                self.assertEqual(mock_logger_warning.call_count, 2)

    @patch('tempfile.NamedTemporaryFile')
    @patch('azure.cognitiveservices.speech.audio.AudioOutputConfig')
    @patch('azure.cognitiveservices.speech.SpeechSynthesizer')
    def test_generate_podcast_synthesis_error(
        self,
        mock_synthesizer_class,
        mock_audio_config,
        mock_temp_file,
    ):
        """Test obsługi błędów syntezy"""
        generator = AzureTTSPodcastGenerator()

        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Test segment',
                'order': 1,
                'speaker': 'Marek',
            },
        ]

        # Mock temp file
        mock_temp_file_instance = Mock()
        mock_temp_file_instance.name = '/tmp/temp_chunk_01.wav'
        mock_temp_file.return_value = mock_temp_file_instance

        # Mock synthesizer z błędem
        mock_synthesizer = Mock()
        mock_result = Mock()
        mock_result.reason = speechsdk.ResultReason.Canceled  # Błąd syntezy
        mock_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_result
        )
        mock_synthesizer_class.return_value = mock_synthesizer

        with patch.object(generator.logger, 'error') as mock_logger_error:
            with patch.object(
                generator,
                '_combine_segments',
                return_value='output.wav',
            ):
                result = generator.generate_podcast_azure(dialog_data)

                mock_logger_error.assert_called_with(
                    'Synthesis error for segment 1',
                )

    @patch('tempfile.NamedTemporaryFile')
    @patch('azure.cognitiveservices.speech.audio.AudioOutputConfig')
    @patch('azure.cognitiveservices.speech.SpeechSynthesizer')
    def test_generate_podcast_exception_handling(
        self,
        mock_synthesizer_class,
        mock_audio_config,
        mock_temp_file,
    ):
        """Test obsługi wyjątków podczas generowania"""
        generator = AzureTTSPodcastGenerator()

        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Test segment',
                'order': 1,
                'speaker': 'Marek',
            },
        ]

        # Mock temp file
        mock_temp_file_instance = Mock()
        mock_temp_file_instance.name = '/tmp/temp_chunk_01.wav'
        mock_temp_file.return_value = mock_temp_file_instance

        # Mock synthesizer rzucający wyjątek
        mock_synthesizer = Mock()
        mock_synthesizer.speak_text_async.side_effect = Exception(
            'Test exception',
        )
        mock_synthesizer_class.return_value = mock_synthesizer

        with patch.object(generator.logger, 'exception') as mock_logger_exception:
            with patch.object(
                generator, '_combine_segments', return_value='output.wav',
            ):
                result = generator.generate_podcast_azure(dialog_data)

                mock_logger_exception.assert_called_once()

    def test_generate_podcast_progress_callback(self):
        """Test wywołań progress callback"""
        generator = AzureTTSPodcastGenerator()

        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Test segment',
                'order': 1,
                'speaker': 'Marek',
            },
        ]

        progress_callback = Mock()

        with patch('tempfile.NamedTemporaryFile'):
            with patch('azure.cognitiveservices.speech.audio.AudioOutputConfig'):
                with patch('azure.cognitiveservices.speech.SpeechSynthesizer'):
                    with patch.object(
                        generator, '_combine_segments', return_value='output.wav',
                    ):
                        generator.generate_podcast_azure(
                            dialog_data, progress_callback=progress_callback,
                        )

                        # Sprawdź wywołania progress callback
                        expected_calls = [
                            call(0, 1, 'Generowanie segmentu 1/1: Marek'),
                            call(1, 1, 'Łączenie segmentów...'),
                        ]
                        progress_callback.assert_has_calls(expected_calls)

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    def test_combine_segments_success(self, mock_exists, mock_wave_open):
        """Test pomyślnego łączenia segmentów"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav', '/tmp/chunk2.wav']
        output_path = '/tmp/output.wav'

        # Mock wave files
        mock_first_wave = Mock()
        mock_params = Mock()
        mock_params.framerate = 22050
        mock_params.sampwidth = 2
        mock_params.nchannels = 1
        mock_first_wave.getparams.return_value = mock_params

        mock_output_wave = Mock()
        mock_temp_wave = Mock()
        mock_temp_wave.getnframes.return_value = 1000
        mock_temp_wave.readframes.return_value = b'audio_data'

        # Konfiguracja mock_wave_open
        def wave_open_side_effect(file, mode):
            if mode == 'rb' and 'chunk1' in file:
                return mock_first_wave
            elif mode == 'rb':
                return mock_temp_wave
            elif mode == 'wb':
                return mock_output_wave

        mock_wave_open.return_value.__enter__ = lambda x: wave_open_side_effect(
            None, None,
        )
        mock_wave_open.side_effect = lambda file, mode: MagicMock(
            __enter__=lambda x: wave_open_side_effect(file, mode),
        )

        with patch('os.remove') as mock_remove:
            result = generator._combine_segments(temp_files, output_path)

            self.assertEqual(result, output_path)

    @patch('os.path.exists', return_value=False)
    def test_combine_segments_no_files(self, mock_exists):
        """Test łączenia segmentów gdy brak plików"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/nonexistent1.wav', '/tmp/nonexistent2.wav']
        output_path = '/tmp/output.wav'

        with patch.object(generator.logger, 'error') as mock_logger_error:
            result = generator._combine_segments(temp_files, output_path)

            self.assertIsNone(result)
            mock_logger_error.assert_called_with(
                'No files to merge - no segments were generated.',
            )

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    def test_combine_segments_wave_exception(
        self,
        mock_exists,
        mock_wave_open,
    ):
        """Test obsługi wyjątku podczas łączenia plików WAV"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock rzucający wyjątek
        mock_wave_open.side_effect = OSError('Wave error')

        with patch.object(generator.logger, 'exception') as mock_logger_exception:
            result = generator._combine_segments(temp_files, output_path)

            self.assertIsNone(result)
            mock_logger_exception.assert_called_once()

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_combine_segments_file_removal_success(
        self, mock_remove, mock_exists, mock_wave_open,
    ):
        """Test pomyślnego usuwania plików tymczasowych"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock wave operations
        self._setup_wave_mocks(mock_wave_open)

        generator._combine_segments(temp_files, output_path)

        mock_remove.assert_called_once_with('/tmp/chunk1.wav')

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch('time.sleep')
    def test_combine_segments_permission_error_retry(
        self, mock_sleep, mock_remove, mock_exists, mock_wave_open,
    ):
        """Test ponawiania usuwania pliku przy błędzie uprawnień"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock wave operations
        self._setup_wave_mocks(mock_wave_open)

        # Mock remove z PermissionError, potem sukces
        mock_remove.side_effect = [PermissionError('Permission denied'), None]

        with patch.object(generator.logger, 'warning') as mock_logger_warning:
            generator._combine_segments(temp_files, output_path)

            self.assertEqual(mock_remove.call_count, 2)
            mock_sleep.assert_called_once_with(1)
            mock_logger_warning.assert_called_once()

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_combine_segments_permission_error_max_retries(
        self, mock_remove, mock_exists, mock_wave_open,
    ):
        """Test maksymalnej liczby prób przy błędzie uprawnień"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock wave operations
        self._setup_wave_mocks(mock_wave_open)

        # Mock remove zawsze zwraca PermissionError
        mock_remove.side_effect = PermissionError('Permission denied')

        with patch.object(generator.logger, 'warning') as mock_logger_warning:
            with patch('time.sleep'):
                generator._combine_segments(temp_files, output_path)

                self.assertEqual(mock_remove.call_count, 3)  # 3 próby
                self.assertEqual(
                    mock_logger_warning.call_count, 3,
                )  # 2 retry warnings + 1 final warning

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_combine_segments_other_remove_exception(
        self, mock_remove, mock_exists, mock_wave_open,
    ):
        """Test obsługi innych wyjątków podczas usuwania plików"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock wave operations
        self._setup_wave_mocks(mock_wave_open)

        # Mock remove rzucający inny wyjątek
        mock_remove.side_effect = OSError('Other error')

        with patch.object(generator.logger, 'error') as mock_logger_error:
            generator._combine_segments(temp_files, output_path)

            mock_logger_error.assert_called_once()

    @patch('wave.open')
    @patch('os.path.exists')
    def test_combine_segments_mixed_file_existence(
        self,
        mock_exists,
        mock_wave_open,
    ):
        """Test łączenia segmentów z mieszanką istniejących i nieistniejących plików"""
        generator = AzureTTSPodcastGenerator()

        temp_files = [
            '/tmp/chunk1.wav',
            '/tmp/nonexistent.wav', '/tmp/chunk2.wav',
        ]
        output_path = '/tmp/output.wav'

        # Mock exists - pierwszy i trzeci plik istnieją
        mock_exists.side_effect = lambda path: 'nonexistent' not in path

        # Mock wave operations
        self._setup_wave_mocks(mock_wave_open)

        with patch('os.remove'):
            result = generator._combine_segments(temp_files, output_path)

            self.assertEqual(result, output_path)

    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    def test_combine_segments_temp_wave_exception(
        self,
        mock_exists,
        mock_wave_open,
    ):
        """Test obsługi wyjątku podczas odczytu pliku tymczasowego"""
        generator = AzureTTSPodcastGenerator()

        temp_files = ['/tmp/chunk1.wav']
        output_path = '/tmp/output.wav'

        # Mock wave contexts
        mock_first_wave = MagicMock()
        mock_params = Mock()
        mock_params.framerate = 22050
        mock_params.sampwidth = 2
        mock_params.nchannels = 1
        mock_first_wave.getparams.return_value = mock_params

        mock_output_wave = MagicMock()

        # Mock temp wave context manager rzucający wyjątek
        mock_temp_wave = MagicMock()
        mock_temp_wave.__enter__.side_effect = OSError('Temp wave error')

        call_count = 0

        def wave_open_side_effect(file, mode):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Pierwszy wywołanie - dla parametrów
                return mock_first_wave
            elif mode == 'rb':  # Temp file read
                return mock_temp_wave
            elif mode == 'wb':  # Output file write
                return mock_output_wave
            return mock_first_wave

        mock_wave_open.side_effect = wave_open_side_effect

        with patch.object(generator.logger, 'warning') as mock_logger_warning:
            with patch('os.remove'):
                result = generator._combine_segments(temp_files, output_path)

                mock_logger_warning.assert_called_once()

    def _setup_wave_mocks(self, mock_wave_open):
        """Pomocnicza metoda do konfiguracji mocków wave"""
        mock_first_wave = MagicMock()
        mock_params = Mock()
        mock_params.framerate = 22050
        mock_params.sampwidth = 2
        mock_params.nchannels = 1
        mock_first_wave.getparams.return_value = mock_params

        mock_output_wave = MagicMock()
        mock_temp_wave = MagicMock()
        mock_temp_wave.getnframes.return_value = 1000
        mock_temp_wave.readframes.return_value = b'audio_data'

        call_count = 0

        def wave_open_side_effect(file, mode):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Pierwszy wywołanie - dla parametrów
                return mock_first_wave
            elif mode == 'rb':  # Temp file read
                return mock_temp_wave
            elif mode == 'wb':  # Output file write
                return mock_output_wave
            return mock_temp_wave

        mock_wave_open.side_effect = wave_open_side_effect


class TestAzureTTSPodcastGeneratorIntegration(unittest.TestCase):
    """Testy integracyjne dla pełnych przepływów"""

    def setUp(self):
        """Przygotowanie środowiska testowego"""
        self.env_patcher = patch.dict(
            os.environ,
            {
                'AZURE_SPEECH_API_KEY': 'test_key',
                'AZURE_SPEECH_REGION': 'test_region',
            },
        )
        self.env_patcher.start()

        self.speech_config_patcher = patch(
            'azure.cognitiveservices.speech.SpeechConfig',
        )
        self.speech_config_patcher.start()

    def tearDown(self):
        """Czyszczenie po testach"""
        self.env_patcher.stop()
        self.speech_config_patcher.stop()

    @patch('tempfile.mkdtemp', return_value='/tmp/podcast_integration')
    @patch(
        'src.utils.logging_config.get_request_id',
        return_value='integration_test',
    )
    @patch('tempfile.NamedTemporaryFile')
    @patch('azure.cognitiveservices.speech.audio.AudioOutputConfig')
    @patch('azure.cognitiveservices.speech.SpeechSynthesizer')
    @patch('wave.open')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch('os.path.join')
    def test_full_podcast_generation_flow(
        self,
        mock_join,
        mock_remove,
        mock_exists,
        mock_wave_open,
        mock_synthesizer_class,
        mock_audio_config,
        mock_temp_file,
        mock_get_request_id,
        mock_mkdtemp,
    ):
        """Test pełnego przepływu generowania podcastu"""
        generator = AzureTTSPodcastGenerator()

        # Mock os.path.join to return expected path
        expected_output = (
            '/tmp/podcast_integration/podcast_integration_test.wav'
        )
        mock_join.return_value = expected_output

        dialog_data = [
            {
                'voice_id': 'pl-PL-MarekNeural',
                'text': 'Witamy w naszym podcaście o testowaniu',
                'order': 1,
                'speaker': 'Marek',
            },
            {
                'voice_id': 'pl-PL-ZofiaNeural',
                'text': 'Dzisiaj porozmawiamy o pokryciu kodu testami',
                'order': 2,
                'speaker': 'Zofia',
            },
        ]

        # Mock temp files
        mock_temp_file_instance = Mock()
        mock_temp_file_instance.name = '/tmp/temp_chunk.wav'
        mock_temp_file.return_value = mock_temp_file_instance

        # Mock synthesizer
        mock_synthesizer = Mock()
        mock_result = Mock()
        mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
        mock_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_result
        )
        mock_synthesizer_class.return_value = mock_synthesizer

        # Mock wave operations
        mock_first_wave = MagicMock()
        mock_params = Mock()
        mock_params.framerate = 22050
        mock_params.sampwidth = 2
        mock_params.nchannels = 1
        mock_first_wave.getparams.return_value = mock_params

        mock_output_wave = MagicMock()
        mock_temp_wave = MagicMock()
        mock_temp_wave.getnframes.return_value = 1000
        mock_temp_wave.readframes.return_value = b'audio_data'

        call_count = 0

        def wave_open_side_effect(file, mode):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Pierwszy wywołanie - dla parametrów
                return mock_first_wave
            elif mode == 'rb':  # Temp file read
                return mock_temp_wave
            elif mode == 'wb':  # Output file write
                return mock_output_wave
            return mock_temp_wave

        mock_wave_open.side_effect = wave_open_side_effect

        # Progress callback mock
        progress_callback = Mock()

        result = generator.generate_podcast_azure(
            dialog_data, progress_callback=progress_callback,
        )

        # Sprawdzenia
        self.assertEqual(result, expected_output)

        # Sprawdź czy synthesizer został wywołany dla każdego segmentu
        self.assertEqual(mock_synthesizer.speak_text_async.call_count, 2)

        # Sprawdź progress callback
        self.assertEqual(
            progress_callback.call_count,
            3,
        )  # 2 segmenty + łączenie
