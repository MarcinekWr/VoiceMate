"""Tests for PdfParser class - Updated to match actual implementation."""

from __future__ import annotations

import os
import shutil
import tempfile
from unittest.mock import Mock, patch, MagicMock

import fitz
import pytest

from src.file_parser.pdf_parser import PdfParser


class TestPdfParser:
    """Test suite for PdfParser class matching actual implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_pdf_file(self, temp_dir):
        """Create mock PDF file."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test PDF content")
        doc.save(pdf_path)
        doc.close()
        return pdf_path

    @pytest.fixture
    def mock_image_describer(self):
        """Create mock ImageDescriber."""
        mock_describer = Mock()
        mock_describer.describe_image.return_value = "Test image description"
        mock_describer.describe_image_from_bytes.return_value = (
            "Test image description from bytes"
        )
        return mock_describer

    @pytest.fixture
    def parser(self, mock_pdf_file, temp_dir):
        """Create PdfParser instance."""
        output_dir = os.path.join(temp_dir, "output")
        return PdfParser(mock_pdf_file, output_dir, describe_images=False)

    @pytest.fixture
    def parser_with_images(self, mock_pdf_file, temp_dir, mock_image_describer):
        """Create PdfParser instance with image description enabled."""
        output_dir = os.path.join(temp_dir, "output")
        return PdfParser(
            mock_pdf_file,
            output_dir,
            describe_images=True,
            image_describer=mock_image_describer,
        )

    def test_init_basic(self, mock_pdf_file, temp_dir):
        """Test basic initialization."""
        output_dir = os.path.join(temp_dir, "output")
        parser = PdfParser(mock_pdf_file, output_dir, describe_images=False)
        assert parser.file_path == mock_pdf_file
        assert parser.describe_images is False
        assert parser.text == ""
        assert parser.images == []
        assert parser.tables == []
        assert parser.structured_content == []
        assert parser.metadata == {}
        assert os.path.exists(output_dir)

    def test_init_with_image_describer(
        self, mock_pdf_file, temp_dir, mock_image_describer
    ):
        """Test initialization with image describer."""
        output_dir = os.path.join(temp_dir, "output")
        parser = PdfParser(
            mock_pdf_file,
            output_dir,
            describe_images=True,
            image_describer=mock_image_describer,
        )
        assert parser.describe_images is True
        assert parser.image_describer == mock_image_describer

    def test_init_with_images_but_no_describer(self, mock_pdf_file, temp_dir):
        """Test initialization with images enabled but no describer provided."""
        output_dir = os.path.join(temp_dir, "output")
        with patch("src.file_parser.pdf_parser.ImageDescriber") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            parser = PdfParser(mock_pdf_file, output_dir, describe_images=True)
            assert parser.describe_images is True
            assert parser.image_describer == mock_instance

    def test_init_output_dir_failure(self, mock_pdf_file):
        """Test output directory creation failure."""
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Failed to create output directory"):
                PdfParser(mock_pdf_file, "some_path")

    def test_extract_metadata_success(self, parser):
        """Test successful metadata extraction."""
        metadata = parser.extract_metadata()
        assert "filename" in metadata
        assert "file_size_mb" in metadata
        assert "page_count" in metadata
        assert metadata["filename"] == "test.pdf"
        assert metadata["page_count"] == 1

    @patch("os.stat", side_effect=OSError("Access denied"))
    def test_extract_metadata_file_error(self, mock_stat, parser):
        """Test metadata extraction file error."""
        metadata = parser.extract_metadata()
        assert "error" in metadata
        assert "Failed to get file stats" in metadata["error"]

    @patch("fitz.open", side_effect=fitz.FileDataError("Invalid PDF"))
    def test_extract_metadata_pdf_error(self, mock_fitz, parser):
        """Test metadata extraction PDF error."""
        with patch("os.stat"):
            metadata = parser.extract_metadata()
        assert "error" in metadata
        assert "Invalid PDF file" in metadata["error"]

    @patch("src.file_parser.pdf_parser.extract_text", return_value="Extracted text")
    def test_extract_text_success(self, mock_extract, parser):
        """Test successful text extraction."""
        result = parser.extract_text()
        assert result == "Extracted text"

    @patch("src.file_parser.pdf_parser.extract_text", side_effect=FileNotFoundError())
    def test_extract_text_file_not_found(self, mock_extract, parser):
        """Test text extraction file not found."""
        result = parser.extract_text()
        assert result == ""

    @patch(
        "src.file_parser.pdf_parser.extract_text",
        side_effect=Exception("Unexpected error"),
    )
    def test_extract_text_general_error(self, mock_extract, parser):
        """Test text extraction general error."""
        result = parser.extract_text()
        assert result == ""

    def test_extract_images_success(self, parser):
        """Test image extraction without description."""
        images = parser.extract_images()
        assert isinstance(images, list)

    def test_extract_images_with_description(self, parser_with_images):
        """Test image extraction with description."""
        # Mock a PDF with images
        with patch("fitz.open") as mock_open:
            mock_doc = Mock()
            mock_page = Mock()
            mock_pixmap = Mock()

            mock_doc.load_page.return_value = mock_page
            mock_page.get_images.return_value = [(123, 0, 100, 100, 0, "", "", "", 0)]

            mock_pixmap.width = 100
            mock_pixmap.height = 100
            mock_pixmap.tobytes.return_value = b"fake_image_data"

            with patch("fitz.Pixmap", return_value=mock_pixmap):
                with patch("builtins.open", mock_open()):
                    with patch(
                        "base64.b64encode", return_value=b"ZmFrZV9pbWFnZV9kYXRh"
                    ):
                        mock_open.return_value = mock_doc
                        images = parser_with_images.extract_images()

            mock_doc.close.assert_called_once()

    @patch("fitz.open", side_effect=fitz.FileDataError("Cannot open"))
    def test_extract_images_open_error(self, mock_fitz, parser):
        """Test image extraction with file open error."""
        images = parser.extract_images()
        assert images == []

    def test_get_image_description_disabled(self, parser):
        """Test image description when disabled."""
        result = parser._get_image_description("test.png", b"fake_data")
        assert result == "No description available"

    def test_get_image_description_success(self, parser_with_images):
        """Test successful image description."""
        result = parser_with_images._get_image_description("test.png", b"fake_data")
        assert result == "Test image description"

    def test_get_image_description_fallback(self, parser_with_images):
        """Test image description fallback to bytes method."""
        parser_with_images.image_describer.describe_image.return_value = (
            "Error generating description"
        )
        result = parser_with_images._get_image_description("test.png", b"fake_data")
        assert result == "Test image description from bytes"

    def test_get_image_description_exception(self, parser_with_images):
        """Test image description with exception."""
        parser_with_images.image_describer.describe_image.side_effect = Exception(
            "Test error"
        )
        result = parser_with_images._get_image_description("test.png", b"fake_data")
        assert result == "Error generating description"

    @patch(
        "src.file_parser.pdf_parser.extract_tables_from_pdf", return_value=[{"page": 1}]
    )
    def test_extract_tables_success(self, mock_extract, parser):
        """Test table extraction."""
        result = parser.extract_tables()
        assert len(result) == 1
        assert result[0]["page"] == 1

    @patch(
        "src.file_parser.pdf_parser.extract_tables_from_pdf",
        side_effect=FileNotFoundError(),
    )
    def test_extract_tables_file_not_found(self, mock_extract, parser):
        """Test table extraction file not found."""
        result = parser.extract_tables()
        assert result == []

    @patch(
        "src.file_parser.pdf_parser.extract_tables_from_pdf", side_effect=Exception()
    )
    def test_extract_tables_error(self, mock_extract, parser):
        """Test table extraction error."""
        result = parser.extract_tables()
        assert result == []

    def test_create_structured_content_success(self, parser):
        """Test structured content creation."""
        parser.images = [{"page": 1, "filename": "test.png"}]
        parser.create_structured_content()
        assert len(parser.structured_content) >= 1
        assert parser.structured_content[0]["page"] == 1

    @patch("fitz.open", side_effect=fitz.FileDataError())
    def test_create_structured_content_error(self, mock_fitz, parser):
        """Test structured content creation error."""
        parser.create_structured_content()
        # Should handle error gracefully and not crash

    def test_parse_all_success(self, parser):
        """Test complete parsing workflow."""
        with patch.object(parser, "extract_metadata", return_value={"pages": 1}):
            with patch.object(parser, "extract_text", return_value="text"):
                with patch.object(parser, "extract_images", return_value=[]):
                    with patch.object(parser, "extract_tables", return_value=[]):
                        with patch.object(parser, "create_structured_content"):
                            result = parser.parse_all()

        assert "text" in result
        assert "images" in result
        assert "tables" in result
        assert "structured_content" in result
        assert "metadata" in result

    def test_parse_all_file_error(self, parser):
        """Test parse_all with file errors."""
        with patch.object(parser, "extract_metadata", side_effect=FileNotFoundError()):
            result = parser.parse_all()
        assert result == {}

    def test_parse_all_memory_error(self, parser):
        """Test parse_all with memory error."""
        with patch.object(parser, "extract_metadata", side_effect=MemoryError()):
            result = parser.parse_all()
        assert result == {}

    def test_parse_all_general_error(self, parser):
        """Test parse_all with general error."""
        with patch.object(parser, "extract_metadata", side_effect=Exception()):
            result = parser.parse_all()
        assert result == {}

    @patch("src.file_parser.pdf_parser.clean_text", return_value="cleaned")
    def test_clean_data_success(self, mock_clean, parser):
        """Test data cleaning."""
        parser.text = "raw text"
        result = parser.clean_data()
        assert result == "cleaned"

    def test_clean_data_no_text(self, parser):
        """Test cleaning with no text."""
        result = parser.clean_data()
        assert result == ""

    @patch(
        "src.file_parser.pdf_parser.clean_text", side_effect=Exception("Clean error")
    )
    def test_clean_data_error(self, mock_clean, parser):
        """Test cleaning with error."""
        parser.text = "text"
        result = parser.clean_data()
        assert result == "text"

    def test_get_content_for_llm_basic(self, parser):
        """Test LLM content generation."""
        parser.text = "test"
        with patch.object(parser, "clean_data", return_value="cleaned"):
            result = parser.get_content_for_llm()
        assert result == "cleaned"

    def test_get_content_for_llm_structured(self, parser):
        """Test LLM content with structured data."""
        parser.metadata = {"filename": "test.pdf", "file_size_mb": 1.5, "page_count": 2}
        parser.structured_content = [
            {
                "page": 1,
                "text": "content",
                "images": [
                    {
                        "filename": "img1.png",
                        "width": 100,
                        "height": 100,
                        "size_kb": 10,
                        "description": "Test image",
                    }
                ],
            },
        ]
        parser.tables = [{"page": 1, "json": '{"data": "test"}'}]

        with patch(
            "src.file_parser.pdf_parser.clean_text", return_value="cleaned content"
        ):
            result = parser.get_content_for_llm()

        assert "DOCUMENT METADATA" in result
        assert "PAGE 1" in result
        assert "TEXT CONTENT" in result
        assert "IMAGES ON THIS PAGE" in result
        assert "TABLES ON THIS PAGE" in result

    def test_save_summary_report_success(self, parser):
        """Test summary report saving."""
        parser.structured_content = [{"page": 1, "text": "test", "images": []}]
        parser.images = []
        parser.text = "text"
        parser.metadata = {"filename": "test.pdf", "file_size_mb": 1.0, "page_count": 1}

        report_path = parser.save_summary_report()
        assert os.path.exists(report_path)

        # Verify content
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "PDF CONTENT EXTRACTION REPORT" in content
            assert "test.pdf" in content

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_summary_report_error(self, mock_open, parser):
        """Test report saving error."""
        with pytest.raises(OSError, match="Failed to save summary report"):
            parser.save_summary_report()

    def test_save_metadata_json_success(self, parser):
        """Test metadata JSON saving."""
        parser.metadata = {"filename": "test.pdf"}
        json_path = parser.save_metadata_json()
        assert os.path.exists(json_path)

        # Verify JSON content
        import json

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["filename"] == "test.pdf"

    def test_save_metadata_json_serialization_error(self, parser):
        """Test JSON serialization error."""
        parser.metadata = {"filename": "test.pdf"}
        with patch("json.dump", side_effect=TypeError("Object not serializable")):
            with pytest.raises(ValueError, match="Failed to serialize"):
                parser.save_metadata_json()
