"""
Tests for PDFImageExtractor class.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, mock_open, patch

import fitz

from src.file_parser.pdf_image_extractor import PDFImageExtractor


class TestPDFImageExtractor(unittest.TestCase):
    """Test suite for the PDFImageExtractor."""

    def setUp(self):
        """Set up common test data and mocks."""
        self.mock_image_describer = MagicMock()
        self.extractor = PDFImageExtractor(
            output_dir='test_output',
            image_describer=self.mock_image_describer,
            describe_images=True,
        )

    @patch('builtins.open', new_callable=mock_open)
    @patch('fitz.Pixmap')
    def test_extract_images_success(self, mock_pixmap, mock_file_open):
        """Test successful image extraction and description."""
        mock_doc = MagicMock(spec=fitz.Document)
        mock_page = MagicMock(spec=fitz.Page)
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_page.get_images.return_value = [(1,)]

        mock_pix = MagicMock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.tobytes.return_value = b'image_data'
        mock_pixmap.return_value = mock_pix

        self.mock_image_describer.describe_image.return_value = 'A nice image.'

        images = self.extractor.extract_images(mock_doc)

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['description'], 'A nice image.')
        mock_file_open.assert_called_once()

    def test_get_image_description_disabled(self):
        """Test that no description is returned when the feature is disabled."""
        self.extractor.describe_images = False
        description = self.extractor._get_image_description('path', b'data')
        self.assertEqual(description, 'No description available')

    def test_get_image_description_fallback(self):
        """Test the fallback to byte-based description on error."""
        self.mock_image_describer.describe_image.return_value = 'Error'
        self.mock_image_describer.describe_image_from_bytes.return_value = (
            'Description from bytes.'
        )

        description = self.extractor._get_image_description('path', b'data')
        self.assertEqual(description, 'Description from bytes.')

    def test_get_image_description_exception(self):
        """Test exception handling during image description."""
        self.mock_image_describer.describe_image.side_effect = Exception(
            'API Error',
        )
        with self.assertRaises(Exception) as exc:
            self.extractor._get_image_description('path', b'data')
        self.assertIn('API Error', str(exc.exception))

    @patch('fitz.Pixmap')
    def test_extract_images_too_small(self, mock_pixmap):
        """Test that small images are skipped."""
        mock_doc = MagicMock(spec=fitz.Document)
        mock_page = MagicMock(spec=fitz.Page)
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_page.get_images.return_value = [(1,)]

        mock_pix = MagicMock()
        mock_pix.width = 40  # Too small
        mock_pix.height = 40
        mock_pixmap.return_value = mock_pix

        images = self.extractor.extract_images(mock_doc)
        self.assertEqual(len(images), 0)
