"""
Tests for LLMService.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.prompts import PromptTemplate

from src.services.llm_service import LLMService


class TestLLMService(unittest.TestCase):
    """Test suite for the LLMService."""

    @patch("src.services.llm_service.setup_logger")
    @patch("src.services.llm_service.AzureChatOpenAI")
    def test_initialization_success(self, mock_azure_llm, mock_setup_logger):
        """Test successful initialization of the LLMService."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        service = LLMService()

        self.assertTrue(service.is_available)
        self.assertIsNotNone(service.llm)
        mock_logger.info.assert_called_with("LLMService setup completed successfully.")

    @patch("src.services.llm_service.setup_logger")
    @patch(
        "src.services.llm_service.AzureChatOpenAI",
        side_effect=Exception("Initialization failed"),
    )
    def test_initialization_failure(self, mock_azure_llm, mock_setup_logger):
        """Test failed initialization of the LLMService."""
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        service = LLMService()

        self.assertFalse(service.is_available)
        self.assertIsNone(service.llm)
        mock_logger.error.assert_called_with(
            "Failed to initialize AzureChatOpenAI: Initialization failed"
        )

    @patch("src.services.llm_service.setup_logger")
    @patch("src.services.llm_service.AzureChatOpenAI")
    def test_generate_description_success(self, mock_azure_llm, mock_setup_logger):
        """Test successful description generation."""
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "A beautiful sunny day."
        mock_llm_instance.invoke.return_value = mock_response
        mock_azure_llm.return_value = mock_llm_instance

        service = LLMService()
        prompt_template = PromptTemplate.from_template("Describe this {topic}.")
        result = service.generate_description(
            "base64_string", prompt_template, "weather"
        )

        self.assertEqual(result, "A beautiful sunny day.")
        mock_llm_instance.invoke.assert_called_once()

    def test_generate_description_service_unavailable(self):
        """Test description generation when the service is not available."""
        with patch.object(LLMService, "_initialize_llm", return_value=None):
            service = LLMService()
            prompt_template = PromptTemplate.from_template("Describe this {topic}.")
            result = service.generate_description(
                "base64_string", prompt_template, "weather"
            )
            self.assertEqual(result, "LLM service not available")


if __name__ == "__main__":
    unittest.main()
