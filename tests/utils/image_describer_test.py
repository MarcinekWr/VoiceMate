"""
Tests for ImageDescriber class.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

from src.utils.image_describer import ImageDescriber


class TestImageDescriber(unittest.TestCase):
    """Test suite for the ImageDescriber class."""

    def setUp(self):
        """Set up a mock for the LLMService."""
        self.patcher = patch('src.utils.image_describer.LLMService')
        self.mock_llm_service_class = self.patcher.start()
        self.mock_llm_service_instance = MagicMock()
        self.mock_llm_service_class.return_value = self.mock_llm_service_instance

    def tearDown(self):
        """Stop the patcher."""
        self.patcher.stop()

    def test_initialization(self):
        """Test that ImageDescriber initializes correctly."""
        self.mock_llm_service_instance.is_available = True
        describer = ImageDescriber()
        self.assertTrue(describer.is_available)
        self.assertIsNotNone(describer.prompt_template)

    def test_initialization_service_unavailable(self):
        """Test initialization when the LLM service is not available."""
        self.mock_llm_service_instance.is_available = False
        describer = ImageDescriber()
        self.assertFalse(describer.is_available)

    def test_describe_image_success(self):
        """Test successful image description."""
        self.mock_llm_service_instance.is_available = True
        self.mock_llm_service_instance.generate_description.return_value = (
            'A detailed description.'
        )

        describer = ImageDescriber()
        with patch(
            'src.utils.image_describer.ImageDescriber._image_to_base64',
            return_value='base64_string',
        ):
            result = describer.describe_image('dummy_path.png')

        self.assertEqual(result, 'A detailed description.')
        self.mock_llm_service_instance.generate_description.assert_called_once()

    def test_describe_image_file_not_found(self):
        """Test image description when the file is not found."""
        self.mock_llm_service_instance.is_available = True
        describer = ImageDescriber()
        with patch(
            'src.utils.image_describer.ImageDescriber._image_to_base64',
            side_effect=FileNotFoundError,
        ):
            result = describer.describe_image('nonexistent.png')
        self.assertIn('file not found', result)

    @patch('builtins.open', new_callable=mock_open, read_data=b'imagedata')
    def test_image_to_base64(self, mock_file):
        """Test the static method _image_to_base64."""
        result = ImageDescriber._image_to_base64('anypath')
        self.assertEqual(result, 'aW1hZ2VkYXRh')
