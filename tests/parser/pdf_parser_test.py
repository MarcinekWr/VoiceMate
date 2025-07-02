"""Tests for PdfParser class - Updated to match actual implementation."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

from src.file_parser.pdf_parser import PdfParser


class TestPdfParser(unittest.TestCase):
    """Test suite for the PdfParser class."""

    def setUp(self):
        """Set up the test environment."""
        self.mock_file_path = 'dummy.pdf'
        self.mock_output_dir = 'test_output'

        self.patchers = {
            'fitz.open': patch('src.file_parser.pdf_parser.fitz.open'),
            'extract_text': patch('src.file_parser.pdf_parser.extract_text'),
            'ImageDescriber': patch(
                'src.file_parser.pdf_parser.ImageDescriber',
            ),
            'PDFImageExtractor': patch(
                'src.file_parser.pdf_parser.PDFImageExtractor',
            ),
            'PDFTableParser': patch(
                'src.file_parser.pdf_parser.PDFTableParser',
            ),
            'PDFContentFormatter': patch(
                'src.file_parser.pdf_parser.PDFContentFormatter',
            ),
            'os.makedirs': patch('os.makedirs'),
            'os.stat': patch('os.stat'),
        }

        self.mocks = {
            name: patcher.start() for name, patcher in self.patchers.items()
        }

        self.mocks['os.stat'].return_value.st_size = 1024 * 1024
        self.mocks['os.stat'].return_value.st_mtime = 1622548800
        self.mocks['extract_text'].return_value = 'Sample text'

        self.mock_image_extractor = self.mocks[
            'PDFImageExtractor'
        ].return_value
        self.mock_table_parser = self.mocks['PDFTableParser'].return_value
        self.mock_formatter = self.mocks['PDFContentFormatter'].return_value

        self.mock_image_extractor.extract_images.return_value = []
        self.mock_table_parser.extract_tables.return_value = []
        self.mock_formatter.create_structured_content.return_value = []
        self.mock_formatter.get_content_for_llm.return_value = 'LLM Content'

    def tearDown(self):
        """Tear down the test environment."""
        for patcher in self.patchers.values():
            patcher.stop()

    def test_initialization(self):
        """Test that PdfParser initializes correctly."""

        parser = PdfParser(self.mock_file_path, self.mock_output_dir)

        self.assertEqual(parser.file_path, self.mock_file_path)
        self.mocks['PDFImageExtractor'].assert_called_with(
            output_dir=self.mock_output_dir,
            image_describer=parser.image_describer,
            describe_images=True,
        )
        self.mocks['PDFTableParser'].assert_called_with(self.mock_file_path)

    def test_parse_all_successful(self):
        """Test the full parsing workflow."""

        parser = PdfParser(self.mock_file_path, self.mock_output_dir)

        result = parser.parse_all()

        self.mocks['fitz.open'].assert_called_with(self.mock_file_path)
        self.mock_image_extractor.extract_images.assert_called_once()
        self.mock_table_parser.extract_tables.assert_called_once()
        self.mocks['PDFContentFormatter'].assert_called_with(
            metadata=result['metadata'],
            images=result['images'],
            tables=result['tables'],
        )
        self.mock_formatter.create_structured_content.assert_called_once()

    def test_parse_all_file_not_found_error(self):
        """Test the parse_all method with a FileNotFoundError."""
        self.mocks['fitz.open'].side_effect = FileNotFoundError
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        result = parser.parse_all()
        self.assertEqual(result, {})

    def test_parse_all_memory_error(self):
        """Test the parse_all method with a MemoryError."""
        self.mocks['fitz.open'].side_effect = MemoryError
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        result = parser.parse_all()
        self.assertEqual(result, {})

    def test_save_summary_report(self):
        """Test the save_summary_report method."""
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        parser.structured_content = [{'page': 1, 'text': '...', 'images': []}]
        with patch('builtins.open', mock_open()) as mocked_file:
            parser.save_summary_report()
            mocked_file.assert_called_once_with(
                os.path.join(self.mock_output_dir, 'extraction_report.txt'),
                'w',
                encoding='utf-8',
            )

    def test_save_metadata_json(self):
        """Test the save_metadata_json method."""
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        parser.metadata = {'key': 'value'}
        with patch('builtins.open', mock_open()) as mocked_file:
            parser.save_metadata_json()
            mocked_file.assert_called_once_with(
                os.path.join(self.mock_output_dir, 'metadata.json'),
                'w',
                encoding='utf-8',
            )

    def test_save_summary_report_os_error(self):
        """Test OSError handling in save_summary_report."""
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        parser.structured_content = [{'page': 1, 'text': '...', 'images': []}]
        with patch('builtins.open', mock_open()) as mocked_file:
            mocked_file.side_effect = OSError('Disk full')
            with self.assertRaises(OSError):
                parser.save_summary_report()

    def test_save_metadata_json_os_error(self):
        """Test OSError handling in save_metadata_json."""
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        parser.metadata = {'key': 'value'}
        with patch('builtins.open', mock_open()) as mocked_file:
            mocked_file.side_effect = OSError('Disk full')
            with self.assertRaises(OSError):
                parser.save_metadata_json()

    def test_save_metadata_json_type_error(self):
        """Test TypeError handling in save_metadata_json."""
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        parser.metadata = {'key': 'value'}
        with (
            patch('builtins.open', mock_open()),
            patch('json.dump', side_effect=TypeError('Not serializable')),
        ):
            with self.assertRaises(ValueError):
                parser.save_metadata_json()

    def test_initiate_workflow(self):
        """Test the end-to-end initiate workflow."""

        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        with (
            patch.object(parser, 'save_summary_report') as mock_save_summary,
            patch.object(parser, 'save_metadata_json') as mock_save_json,
            patch.object(parser, 'save_llm_content') as mock_save_llm,
        ):
            content = parser.initiate()

            self.assertEqual(content, 'LLM Content')
            mock_save_summary.assert_called_once()
            mock_save_json.assert_called_once()
            mock_save_llm.assert_called_with('LLM Content')

    def test_extract_metadata_os_error(self):
        """Test os.stat error handling in extract_metadata."""
        self.mocks['os.stat'].side_effect = OSError('Permission denied')
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        metadata = parser.extract_metadata(MagicMock())
        self.assertIn('error', metadata)

    def test_extract_metadata_runtime_error(self):
        """Test RuntimeError handling in extract_metadata."""

        mock_doc = MagicMock()
        mock_doc.metadata = {'title': 'Test'}
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)

        with patch.object(
            mock_doc,
            'close',
            side_effect=RuntimeError("Can't close"),
        ):
            metadata = parser.extract_metadata(mock_doc)
            # should still get metadata before error
            self.assertIn('title', metadata)

    def test_extract_text_file_not_found(self):
        """Test FileNotFoundError in extract_text."""
        self.mocks['extract_text'].side_effect = FileNotFoundError
        parser = PdfParser(self.mock_file_path, self.mock_output_dir)
        result = parser.extract_text()
        self.assertEqual(result, '')
