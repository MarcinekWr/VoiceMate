from __future__ import annotations

import os
import unittest
from unittest.mock import patch, mock_open, MagicMock

import src.logic.llm_podcast as pipeline


class TestLLMPipeline(unittest.TestCase):
    def test_validate_env_variables_all_set(self):
        with patch.dict(
            os.environ,
            {
                'AZURE_OPENAI_ENDPOINT': 'url',
                'AZURE_OPENAI_API_KEY': 'key',
                'API_VERSION': '2024-06-01',
                'AZURE_OPENAI_DEPLOYMENT': 'deployment',
                'AZURE_OPENAI_MODEL': 'model',
            },
        ):
            try:
                pipeline.validate_env_variables()
            except ValueError:
                self.fail('Unexpected ValueError')

    def test_validate_env_variables_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                pipeline.validate_env_variables()
            self.assertIn(
                'Missing required environment variables',
                str(ctx.exception),
            )

    @patch('src.logic.llm_podcast.AzureChatOpenAI')
    @patch('src.logic.llm_podcast.validate_env_variables')
    def test_create_llm_success(self, mock_validate, mock_azure):
        mock_azure.return_value = MagicMock()
        llm = pipeline.create_llm()
        self.assertTrue(mock_validate.called)
        self.assertTrue(mock_azure.called)
        self.assertIsNotNone(llm)



    @patch("src.logic.llm_podcast.PROMPT_PATHS", {"plan": "fake_path.txt"})
    @patch("os.path.isfile", return_value=False)
    def test_load_prompt_template_file_not_found(self, mock_isfile):
        with self.assertRaises(FileNotFoundError):
            pipeline.load_prompt_template('plan')


    @patch("src.logic.llm_podcast.PROMPT_PATHS", {"plan": "dummy.txt"})
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="Plan: {input_text}")
    def test_load_prompt_template_success(self, mock_file, mock_isfile):
        template = pipeline.load_prompt_template("plan")
        result = template.format(input_text="test")
        self.assertIn("test", result)


    @patch("src.logic.llm_podcast.load_prompt_template")
    def test_generate_plan_success(self, mock_prompt):
        fake_llm = MagicMock()
        fake_llm.invoke.return_value.content = 'Plan result'
        mock_prompt.return_value.format.return_value = 'formatted prompt'

        result = pipeline.generate_plan(fake_llm, 'input')
        self.assertEqual(result, 'Plan result')

    def test_generate_plan_empty_input(self):
        with self.assertRaises(ValueError):
            pipeline.generate_plan(MagicMock(), ' ')

    @patch('src.logic.llm_podcast.load_prompt_template')
    def test_generate_podcast_text_success(self, mock_prompt):
        fake_llm = MagicMock()
        fake_llm.invoke.return_value.content = 'Podcast output'
        mock_prompt.return_value.format.return_value = 'user_prompt'

        result = pipeline.generate_podcast_text(
            fake_llm, 'scientific', 'input', 'plan',
        )
        self.assertIn('Podcast output', result)

    def test_generate_podcast_text_missing_input_or_plan(self):
        fake_llm = MagicMock()
        with self.assertRaises(ValueError):
            pipeline.generate_podcast_text(fake_llm, 'casual', '', 'plan')
        with self.assertRaises(ValueError):
            pipeline.generate_podcast_text(fake_llm, 'casual', 'text', '')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_to_file_success(self, mock_file):
        pipeline.save_to_file('data', 'file.txt')
        mock_file.assert_called_once_with('file.txt', 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('data')

    @patch('builtins.open', side_effect=Exception('write error'))
    def test_save_to_file_exception(self, mock_file):
        with self.assertRaises(Exception):
            pipeline.save_to_file('data', 'file.txt')

    @patch('src.logic.llm_podcast.create_llm')
    def test_llm_podcast_service_init(self, mock_create_llm):
        service = pipeline.LLMPodcastService()
        self.assertTrue(hasattr(service, 'llm'))
        mock_create_llm.assert_called_once()

    @patch('src.logic.llm_podcast.save_to_file')
    @patch('src.logic.llm_podcast.generate_podcast_text', return_value='Podcast')
    @patch('src.logic.llm_podcast.generate_plan', return_value='Plan')
    @patch('src.logic.llm_podcast.create_llm')
    def test_llm_podcast_service_run_success(
        self, mock_llm, mock_plan, mock_podcast, mock_save,
    ):
        fake_input_path = "src/logic/llm_text_test_file.txt"
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="Input Text")),
        ):

            service = pipeline.LLMPodcastService()
            service.run()

            mock_plan.assert_called_once()
            mock_podcast.assert_called_once()
            self.assertEqual(mock_save.call_count, 2)
