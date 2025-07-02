import unittest
from unittest.mock import MagicMock, patch

from langchain_core.prompts import PromptTemplate
from src.services.llm_service import LLMService


class TestLLMService(unittest.TestCase):
    """Test suite for the LLMService."""

    @patch('src.services.llm_service.get_secret_env_first')
    @patch('src.services.llm_service.AzureChatOpenAI')
    def test_initialization_success(self, mock_azure_llm, mock_get_secret):
        """Test successful initialization of the LLMService."""
        mock_get_secret.return_value = "dummy"  # simulate secrets
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        service = LLMService()

        self.assertTrue(service.is_available)
        self.assertIs(service.llm, mock_llm_instance)

    @patch('src.services.llm_service.get_secret_env_first', side_effect=Exception("Secret error"))
    @patch('src.services.llm_service.AzureChatOpenAI')
    def test_initialization_failure(self, mock_azure_llm, mock_get_secret):
        """Test failed initialization of the LLMService due to missing secrets."""
        service = LLMService()

        self.assertFalse(service.is_available)
        self.assertIsNone(service.llm)

    @patch('src.services.llm_service.get_secret_env_first')
    @patch('src.services.llm_service.AzureChatOpenAI')
    def test_generate_description_success(self, mock_azure_llm, mock_get_secret):
        """Test successful description generation."""
        mock_get_secret.return_value = "dummy"
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = 'A beautiful sunny day.'
        mock_llm_instance.invoke.return_value = mock_response
        mock_azure_llm.return_value = mock_llm_instance

        service = LLMService()
        prompt_template = PromptTemplate.from_template('Describe this {topic}.')

        result = service.generate_description('base64_string', prompt_template, 'weather')

        self.assertEqual(result, 'A beautiful sunny day.')
        mock_llm_instance.invoke.assert_called_once()

    def test_generate_description_service_unavailable(self):
        """Test description generation when the service is not available."""
        with patch.object(LLMService, '_initialize_llm', return_value=None):
            service = LLMService()
            prompt_template = PromptTemplate.from_template('Describe this {topic}.')
            result = service.generate_description('base64_string', prompt_template, 'weather')
            self.assertEqual(result, 'LLM service not available')


if __name__ == '__main__':
    unittest.main()
