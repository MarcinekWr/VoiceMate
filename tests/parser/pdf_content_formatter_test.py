"""
Tests for PDFContentFormatter class.
"""

import unittest
from unittest.mock import MagicMock, patch

import fitz

from src.file_parser.pdf_content_formatter import PDFContentFormatter
from src.utils.text_cleaner import TextCleaner


class TestPDFContentFormatter(unittest.TestCase):
    """Test suite for the PDFContentFormatter."""

    def setUp(self):
        """Set up common test data."""
        self.mock_metadata = {"filename": "test.pdf", "page_count": 1}
        self.mock_images = [
            {
                "page": 1,
                "filename": "image1.png",
                "width": 100,
                "height": 100,
                "size_kb": 50,
                "description": "An image.",
            }
        ]
        self.mock_tables = [{"page": 1, "json": '{"key": "value"}'}]
        self.formatter = PDFContentFormatter(
            self.mock_metadata, self.mock_images, self.mock_tables
        )

    @patch("fitz.open")
    def test_create_structured_content(self, mock_fitz_open):
        """Test the creation of structured content from a PDF."""
        mock_doc = MagicMock(spec=fitz.Document)
        mock_page = MagicMock(spec=fitz.Page)
        mock_page.get_text.return_value = "Page text"
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        content = self.formatter.create_structured_content(mock_doc)

        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["page"], 1)
        self.assertEqual(content[0]["text"], "Page text")
        self.assertEqual(len(content[0]["images"]), 1)

    @patch("fitz.open")
    def test_create_structured_content_runtime_error(self, mock_fitz_open):
        """Test handling of a RuntimeError during text extraction."""
        mock_doc = MagicMock(spec=fitz.Document)
        mock_page = MagicMock(spec=fitz.Page)
        mock_page.get_text.side_effect = RuntimeError("Failed to get text")
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        content = self.formatter.create_structured_content(mock_doc)

        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["text"], "")

    def test_get_content_for_llm_no_structured_content(self):
        """Test LLM content generation when there is no structured content."""
        self.formatter.structured_content = []
        result = self.formatter.get_content_for_llm()
        self.assertEqual(result, "")

    @patch("src.utils.text_cleaner.TextCleaner.clean_text")
    def test_get_content_for_llm_with_all_data(self, mock_clean_text):
        """Test LLM content generation with all data types present."""
        mock_clean_text.return_value = "Cleaned text."
        self.formatter.structured_content = [
            {
                "page": 1,
                "text": "Page text",
                "images": self.mock_images,
            }
        ]

        result = self.formatter.get_content_for_llm()

        self.assertIn("--- DOCUMENT METADATA ---", result)
        self.assertIn("--- PAGE 1 ---", result)
        self.assertIn("TEXT CONTENT", result)
        self.assertIn("Cleaned text.", result)
        self.assertIn("IMAGES ON THIS PAGE", result)
        self.assertIn("An image.", result)
        self.assertIn("TABLES ON THIS PAGE", result)
        self.assertIn('{"key": "value"}', result)

    @patch("src.utils.text_cleaner.TextCleaner.clean_text")
    def test_get_content_for_llm_cleaning_error(self, mock_clean_text):
        """Test LLM content generation with a text cleaning error."""
        mock_clean_text.side_effect = Exception("Cleaning failed")
        self.formatter.structured_content = [
            {"page": 1, "text": "Dirty text", "images": []}
        ]

        result = self.formatter.get_content_for_llm()
        self.assertIn("Dirty text", result)
