from __future__ import annotations

"""Tests for ImageDescriber class with ~80% coverage."""
import base64
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image

from src.utils.image_describer import ImageDescriber


class TestImageDescriber:
    """Test suite for ImageDescriber class."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for Azure OpenAI."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_API_KEY": "test-api-key",
                "API_VERSION": "2024-02-15-preview",
                "AZURE_OPENAI_DEPLOYMENT": "gpt-4-vision",
                "AZURE_OPENAI_MODEL": "gpt-4-vision-preview",
            },
        ):
            yield

    @pytest.fixture
    def mock_prompt_file(self):
        """Create a temporary prompt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Custom prompt: Describe the image with focus on {topic}")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_image_path(self):
        """Create a temporary sample image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a simple test image
            img = Image.new("RGB", (100, 100), color="red")
            img.save(f.name, "PNG")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes."""
        img = Image.new("RGB", (50, 50), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_init_successful_setup(self, mock_env_vars):
        """Test successful initialization with all dependencies available."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber()

            assert describer.is_available is True
            assert describer.llm is not None
            assert describer.prompt_template is not None
            mock_llm.assert_called_once()

    def test_init_with_custom_prompt_path(self, mock_env_vars, mock_prompt_file):
        """Test initialization with custom prompt file."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber(prompt_path=mock_prompt_file)

            assert describer.is_available is True
            assert describer.prompt_path == mock_prompt_file

    def test_init_import_error(self, mock_env_vars):
        """Test initialization when langchain_openai import fails."""
        with patch(
            "src.utils.image_describer.AzureChatOpenAI",
            side_effect=ImportError("Module not found"),
        ):
            describer = ImageDescriber()

            assert describer.is_available is False
            assert describer.llm is None

    def test_init_unexpected_error(self, mock_env_vars):
        """Test initialization with unexpected error."""
        with patch(
            "src.utils.image_describer.AzureChatOpenAI",
            side_effect=Exception("Unexpected error"),
        ):
            describer = ImageDescriber()

            assert describer.is_available is False
            assert describer.llm is None

    def test_load_prompt_template_custom_file(self, mock_env_vars, mock_prompt_file):
        """Test loading custom prompt template from file."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber(prompt_path=mock_prompt_file)

            mock_prompt.from_template.assert_called()
            call_args = mock_prompt.from_template.call_args[0][0]
            assert "Custom prompt" in call_args

    def test_load_prompt_template_file_not_found(self, mock_env_vars):
        """Test loading prompt template when file doesn't exist."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber(prompt_path="nonexistent_file.txt")

            mock_prompt.from_template.assert_called()
            call_args = mock_prompt.from_template.call_args[0][0]
            assert "Describe this image in detail" in call_args

    def test_load_prompt_template_read_error(self, mock_env_vars):
        """Test loading prompt template when file read fails."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
            patch(
                "pathlib.Path.read_text",
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error"),
            ),
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                temp_path = f.name

            try:
                describer = ImageDescriber(prompt_path=temp_path)

                mock_prompt.from_template.assert_called()
                call_args = mock_prompt.from_template.call_args[0][0]
                assert "Describe this image in detail" in call_args
            finally:
                os.unlink(temp_path)

    def test_describe_image_success(self, mock_env_vars, sample_image_path):
        """Test successful image description."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            # Setup mocks
            mock_llm_instance = Mock()
            mock_response = Mock()
            mock_response.content = "A red square image"
            mock_llm_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Describe this image"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber()
            result = describer.describe_image(sample_image_path)

            assert result == "A red square image"
            mock_llm_instance.invoke.assert_called_once()

    def test_describe_image_not_available(self):
        """Test image description when service is not available."""
        with patch(
            "src.utils.image_describer.AzureChatOpenAI", side_effect=ImportError()
        ):
            describer = ImageDescriber()
            result = describer.describe_image("any_path.jpg")

            assert result == "Image description not available"

    def test_describe_image_file_not_found(self, mock_env_vars):
        """Test image description with non-existent file."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber()
            result = describer.describe_image("nonexistent_file.jpg")

            assert "Image description not available - file not found" in result

    def test_describe_image_unexpected_error(self, mock_env_vars, sample_image_path):
        """Test image description with unexpected error."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.side_effect = Exception("API Error")
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Describe this image"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber()
            result = describer.describe_image(sample_image_path)

            assert "Error generating description: API Error" in result

    def test_image_to_base64(self, mock_env_vars, sample_image_path):
        """Test image to base64 conversion."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber()
            base64_result = describer._image_to_base64(sample_image_path)

            decoded = base64.b64decode(base64_result)
            assert len(decoded) > 0

            assert decoded.startswith(b"\x89PNG")

    def test_describe_image_from_bytes_success(self, mock_env_vars, sample_image_bytes):
        """Test successful image description from bytes."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm_instance = Mock()
            mock_response = Mock()
            mock_response.content = "A blue square image"
            mock_llm_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Describe this image"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber()
            result = describer.describe_image_from_bytes(sample_image_bytes)

            assert result == "A blue square image"
            mock_llm_instance.invoke.assert_called_once()

    def test_describe_image_from_bytes_not_available(self, sample_image_bytes):
        """Test image description from bytes when service is not available."""
        with patch(
            "src.utils.image_describer.AzureChatOpenAI", side_effect=ImportError()
        ):
            describer = ImageDescriber()
            result = describer.describe_image_from_bytes(sample_image_bytes)

            assert result == "Image description not available"

    def test_describe_image_from_bytes_error(self, mock_env_vars, sample_image_bytes):
        """Test image description from bytes with error."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.side_effect = Exception("Processing error")
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Describe this image"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber()
            result = describer.describe_image_from_bytes(sample_image_bytes)

            assert "Error generating description: Processing error" in result

    def test_use_default_prompt(self, mock_env_vars):
        """Test the default prompt setup."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            describer = ImageDescriber()
            describer._use_default_prompt()

            mock_prompt.from_template.assert_called()
            call_args = mock_prompt.from_template.call_args[0][0]
            assert "Describe this image in detail" in call_args
            assert "charts, diagrams" in call_args

    @patch("src.utils.image_describer.logger")
    def test_logging_calls(self, mock_logger, mock_env_vars):
        """Test that appropriate logging calls are made."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            mock_llm.return_value = Mock()
            mock_prompt.from_template.return_value = Mock()

            ImageDescriber()

            mock_logger.info.assert_called()
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any(
                "ImageDescriber setup completed successfully" in call
                for call in info_calls
            )

    def test_message_content_structure(self, mock_env_vars, sample_image_path):
        """Test that the message content has the correct structure for LLM."""
        with (
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
            patch("src.utils.image_describer.HumanMessage") as mock_message,
        ):
            mock_llm_instance = Mock()
            mock_response = Mock()
            mock_response.content = "Test response"
            mock_llm_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Test prompt"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber()
            describer.describe_image(sample_image_path)

            mock_message.assert_called_once()
            call_args = mock_message.call_args[1]["content"]

            assert len(call_args) == 2
            assert call_args[0]["type"] == "text"
            assert call_args[0]["text"] == "Test prompt"
            assert call_args[1]["type"] == "image_url"
            assert "data:image/png;base64," in call_args[1]["image_url"]["url"]


# Additional integration-style tests
class TestImageDescriberIntegration:
    """Integration tests for ImageDescriber."""

    def test_end_to_end_flow_with_mocked_azure(self, tmp_path):
        """Test the complete flow with all components mocked."""
        test_image = tmp_path / "test.png"
        img = Image.new("RGB", (10, 10), color="green")
        img.save(str(test_image))

        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("Test prompt template")

        with (
            patch.dict(
                os.environ,
                {
                    "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                    "AZURE_OPENAI_API_KEY": "test-key",
                    "API_VERSION": "2024-02-15-preview",
                    "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
                    "AZURE_OPENAI_MODEL": "test-model",
                },
            ),
            patch("src.utils.image_describer.AzureChatOpenAI") as mock_llm,
            patch("src.utils.image_describer.PromptTemplate") as mock_prompt,
        ):
            # Setup complete mock chain
            mock_llm_instance = Mock()
            mock_response = Mock()
            mock_response.content = "A small green square"
            mock_llm_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_llm_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.format.return_value = "Test prompt template"
            mock_prompt.from_template.return_value = mock_prompt_instance

            describer = ImageDescriber(prompt_path=str(prompt_file))

            assert describer.is_available is True

            result = describer.describe_image(str(test_image))
            assert result == "A small green square"

            with open(str(test_image), "rb") as f:
                image_bytes = f.read()

            result_bytes = describer.describe_image_from_bytes(image_bytes)
            assert result_bytes == "A small green square"
