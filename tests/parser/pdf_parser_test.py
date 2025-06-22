"""Tests for PdfParser class - Enhanced coverage to reach 73%+ in 230 lines."""
from __future__ import annotations

import os
import shutil
import tempfile
from unittest.mock import Mock
from unittest.mock import patch

import fitz
import pytest

from src.file_parser.pdf_parser import PdfParser


class TestPdfParser:
    """Enhanced test suite for PdfParser class targeting 73%+ coverage."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_pdf_file(self, temp_dir):
        """Create mock PDF file."""
        pdf_path = os.path.join(temp_dir, 'test.pdf')
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), 'Test PDF content')
        doc.save(pdf_path)
        doc.close()
        return pdf_path

    @pytest.fixture
    def parser(self, mock_pdf_file, temp_dir):
        """Create PdfParser instance."""
        output_dir = os.path.join(temp_dir, 'output')
        return PdfParser(mock_pdf_file, output_dir, describe_images=False)

    def test_init_basic(self, mock_pdf_file, temp_dir):
        """Test basic initialization."""
        output_dir = os.path.join(temp_dir, 'output')
        with patch.object(PdfParser, 'setup_image_describer'):
            parser = PdfParser(mock_pdf_file, output_dir)
        assert parser.file_path == mock_pdf_file
        assert parser.describe_images is True
        assert parser.text == ''
        assert parser.images == []
        assert os.path.exists(output_dir)

    def test_init_output_dir_failure(self, mock_pdf_file):
        """Test output directory creation failure."""
        with patch(
            'os.makedirs',
            side_effect=OSError('Permission denied'),
        ):
            with pytest.raises(
                OSError,
                match='Failed to create output directory',
            ):
                PdfParser(mock_pdf_file, 'some_path')

    @patch.dict(
        os.environ,
        {
            'AZURE_OPENAI_ENDPOINT': 'test',
            'AZURE_OPENAI_API_KEY': 'test',
        },
    )
    @patch('src.file_parser.pdf_parser.AzureChatOpenAI')
    def test_setup_image_describer_success_with_prompt(
        self,
        mock_azure,
        parser,
    ):
        """Test successful setup with custom prompt file."""
        parser.describe_images = True
        mock_azure.return_value = Mock()
        with patch(
            'src.file_parser.pdf_parser.os.path.exists',
            return_value=True,
        ):
            with patch('src.file_parser.pdf_parser.Path') as mock_path:
                mock_path.return_value.read_text.return_value = 'Custom prompt'
                parser.setup_image_describer()
        assert parser.llm is not None

    @patch.dict(
        os.environ,
        {
            'AZURE_OPENAI_ENDPOINT': 'test',
            'AZURE_OPENAI_API_KEY': 'test',
        },
    )
    @patch('src.file_parser.pdf_parser.AzureChatOpenAI')
    def test_setup_image_describer_no_prompt_file(
        self,
        mock_azure,
        parser,
    ):
        """Test setup without custom prompt file."""
        parser.describe_images = True
        mock_azure.return_value = Mock()
        with patch(
            'src.file_parser.pdf_parser.os.path.exists',
            return_value=False,
        ):
            parser.setup_image_describer()
        assert parser.llm is not None

    @patch.dict(
        os.environ,
        {
            'AZURE_OPENAI_ENDPOINT': 'test',
            'AZURE_OPENAI_API_KEY': 'test',
        },
    )
    @patch('src.file_parser.pdf_parser.AzureChatOpenAI')
    def test_setup_image_describer_prompt_errors(
        self,
        mock_azure,
        parser,
    ):
        """Test setup with prompt file read errors."""
        parser.describe_images = True
        mock_azure.return_value = Mock()
        with patch(
            'src.file_parser.pdf_parser.os.path.exists',
            return_value=True,
        ):
            with patch('src.file_parser.pdf_parser.Path') as mock_path:
                mock_path.return_value.read_text.side_effect = OSError(
                    'Permission denied',
                )
                parser.setup_image_describer()
        assert parser.llm is not None

    @patch(
        'src.file_parser.pdf_parser.AzureChatOpenAI',
        side_effect=ImportError(),
    )
    def test_setup_image_describer_import_error(
        self,
        mock_azure,
        parser,
    ):
        """Test import error handling."""
        parser.describe_images = True
        parser.setup_image_describer()
        assert parser.describe_images is False

    @patch.dict(
        os.environ,
        {
            'AZURE_OPENAI_ENDPOINT': 'test',
            'AZURE_OPENAI_API_KEY': 'test',
        },
    )
    @patch(
        'src.file_parser.pdf_parser.AzureChatOpenAI',
        side_effect=Exception('Setup failed'),
    )
    def test_setup_image_describer_general_error(
        self,
        mock_azure,
        parser,
    ):
        """Test general exception handling."""
        parser.describe_images = True
        parser.setup_image_describer()
        assert parser.describe_images is False

    def test_describe_image_disabled(self, parser):
        """Test image description when disabled."""
        result = parser.describe_image('dummy.png')
        assert result == 'Image description not available'

    @patch('src.file_parser.pdf_parser.Image')
    @patch('os.path.exists', return_value=True)
    @patch('base64.b64encode', return_value=b'encoded')
    def test_describe_image_success(
        self,
        mock_b64,
        mock_exists,
        mock_image,
        parser,
    ):
        """Test successful image description."""
        parser.describe_images = True
        parser.llm = Mock()
        parser.prompt_template = Mock()
        parser.prompt_template.format.return_value = 'Describe'
        parser.llm.invoke.return_value.content = 'Test description'
        mock_image.open.return_value.__enter__.return_value = Mock()

        result = parser.describe_image('test.png')
        assert result == 'Test description'

    def test_describe_image_file_not_found(self, parser):
        """Test image description with missing file."""
        parser.describe_images = True
        parser.llm = Mock()
        parser.prompt_template = Mock()
        with patch('os.path.exists', return_value=False):
            result = parser.describe_image('missing.png')
        assert result == 'Image description not available'

    def test_describe_image_exception_handling(self, parser):
        """Test image description exception handling."""
        parser.describe_images = True
        parser.llm = Mock()
        parser.prompt_template = Mock()
        with patch('os.path.exists', return_value=True):
            with patch(
                'src.file_parser.pdf_parser.Image.open',
                side_effect=Exception('IO Error'),
            ):
                result = parser.describe_image('test.png')
        assert 'Error generating description' in result

    def test_extract_metadata_success(self, parser):
        """Test successful metadata extraction."""
        metadata = parser.extract_metadata()
        assert 'filename' in metadata
        assert 'file_size_mb' in metadata
        assert 'page_count' in metadata
        assert metadata['filename'] == 'test.pdf'

    @patch('os.stat', side_effect=OSError('Access denied'))
    def test_extract_metadata_file_error(
        self,
        mock_stat,
        parser,
    ):
        """Test metadata extraction file error."""
        metadata = parser.extract_metadata()
        assert 'error' in metadata

    @patch('fitz.open', side_effect=fitz.FileDataError('Invalid PDF'))
    def test_extract_metadata_pdf_error(
        self,
        mock_fitz,
        parser,
    ):
        """Test metadata extraction PDF error."""
        with patch('os.stat'):
            metadata = parser.extract_metadata()
        assert 'error' in metadata

    @patch(
        'src.file_parser.pdf_parser.extract_text',
        return_value='Extracted text',
    )
    def test_extract_text_success(
        self,
        mock_extract,
        parser,
    ):
        """Test successful text extraction."""
        result = parser.extract_text()
        assert result == 'Extracted text'

    @patch(
        'src.file_parser.pdf_parser.extract_text',
        side_effect=FileNotFoundError(),
    )
    def test_extract_text_file_not_found(
        self,
        mock_extract,
        parser,
    ):
        """Test text extraction file not found."""
        result = parser.extract_text()
        assert result == ''

    @patch(
        'src.file_parser.pdf_parser.extract_text',
        side_effect=Exception('Unexpected error'),
    )
    def test_extract_text_general_error(
        self,
        mock_extract,
        parser,
    ):
        """Test text extraction general error."""
        result = parser.extract_text()
        assert result == ''

    def test_extract_images_success(self, parser):
        """Test image extraction."""
        images = parser.extract_images()
        assert isinstance(images, list)

    @patch(
        'fitz.open',
        side_effect=fitz.FileDataError('Cannot open'),
    )
    def test_extract_images_open_error(self, mock_fitz, parser):
        """Test image extraction with file open error."""
        images = parser.extract_images()
        assert images == []

    @patch(
        'src.file_parser.pdf_parser.extract_tables_from_pdf',
        return_value=[{'page': 1}],
    )
    def test_extract_tables_success(
        self,
        mock_extract,
        parser,
    ):
        """Test table extraction."""
        result = parser.extract_tables()
        assert len(result) == 1

    @patch(
        'src.file_parser.pdf_parser.extract_tables_from_pdf',
        side_effect=FileNotFoundError(),
    )
    def test_extract_tables_file_not_found(
        self,
        mock_extract,
        parser,
    ):
        """Test table extraction file not found."""
        result = parser.extract_tables()
        assert result == []

    @patch(
        'src.file_parser.pdf_parser.extract_tables_from_pdf',
        side_effect=Exception(),
    )
    def test_extract_tables_error(self, mock_extract, parser):
        """Test table extraction error."""
        result = parser.extract_tables()
        assert result == []

    def test_create_structured_content_success(self, parser):
        """Test structured content creation."""
        parser.images = [{'page': 1, 'filename': 'test.png'}]
        parser.create_structured_content()
        assert len(parser.structured_content) >= 1

    @patch('fitz.open', side_effect=fitz.FileDataError())
    def test_create_structured_content_error(self, mock_fitz, parser):
        """Test structured content creation error."""
        parser.create_structured_content()
        assert parser.structured_content == []

    def test_parse_all_success(self, parser):
        """Test complete parsing workflow."""
        with patch.object(
            parser,
            'extract_metadata',
            return_value={'pages': 1},
        ):
            with patch.object(
                parser,
                'extract_text',
                return_value='text',
            ):
                with patch.object(
                    parser,
                    'extract_images',
                    return_value=[],
                ):
                    with patch.object(
                        parser,
                        'extract_tables',
                        return_value=[],
                    ):
                        with patch.object(
                            parser,
                            'create_structured_content',
                        ):
                            result = parser.parse_all()
        assert 'text' in result
        assert 'images' in result
        assert 'metadata' in result

    def test_parse_all_file_error(self, parser):
        """Test parse_all with file errors."""
        with patch.object(
            parser,
            'extract_metadata',
            side_effect=FileNotFoundError(),
        ):
            result = parser.parse_all()
        assert result is None

    def test_parse_all_memory_error(self, parser):
        """Test parse_all with memory error."""
        with patch.object(
            parser,
            'extract_metadata',
            side_effect=MemoryError(),
        ):
            result = parser.parse_all()
        assert result is None

    def test_parse_all_general_error(self, parser):
        """Test parse_all with general error."""
        with patch.object(
            parser,
            'extract_metadata',
            side_effect=Exception(),
        ):
            result = parser.parse_all()
        assert result is None

    @patch(
        'src.file_parser.pdf_parser.clean_text',
        return_value='cleaned',
    )
    def test_clean_data_success(self, mock_clean, parser):
        """Test data cleaning."""
        parser.text = 'raw text'
        result = parser.clean_data()
        assert result == 'cleaned'

    def test_clean_data_no_text(self, parser):
        """Test cleaning with no text."""
        result = parser.clean_data()
        assert result == ''

    @patch(
        'src.file_parser.pdf_parser.clean_text',
        side_effect=Exception('Clean error'),
    )
    def test_clean_data_error(self, mock_clean, parser):
        """Test cleaning with error."""
        parser.text = 'text'
        result = parser.clean_data()
        assert result == 'text'

    def test_get_content_for_llm_basic(self, parser):
        """Test LLM content generation."""
        parser.text = 'test'
        with patch.object(
            parser,
            'clean_data',
            return_value='cleaned',
        ):
            result = parser.get_content_for_llm()
        assert result == 'cleaned'

    def test_get_content_for_llm_structured(self, parser):
        """Test LLM content with structured data."""
        parser.metadata = {'filename': 'test.pdf'}
        parser.structured_content = [
            {'page': 1, 'text': 'content', 'images': []},
        ]
        parser.tables = [{'page': 1, 'json': '{}'}]

        with patch(
            'src.file_parser.pdf_parser.clean_text',
            return_value='cleaned',
        ):
            result = parser.get_content_for_llm()

        assert 'METADATA' in result
        assert 'PAGE 1' in result

    def test_save_summary_report_success(self, parser):
        """Test summary report saving."""
        parser.structured_content = [{'page': 1, 'text': 'test', 'images': []}]
        parser.images = []
        parser.text = 'text'
        parser.metadata = {'filename': 'test.pdf'}

        report_path = parser.save_summary_report()
        assert os.path.exists(report_path)

    @patch('builtins.open', side_effect=OSError())
    def test_save_summary_report_error(
        self,
        mock_open,
        parser,
    ):
        """Test report saving error."""
        with pytest.raises(OSError, match='Failed to save summary report'):
            parser.save_summary_report()

    def test_save_metadata_json_success(self, parser):
        """Test metadata JSON saving."""
        parser.metadata = {'filename': 'test.pdf'}
        json_path = parser.save_metadata_json()
        assert os.path.exists(json_path)

    def test_save_metadata_json_serialization_error(self, parser):
        """Test JSON serialization error."""
        parser.metadata = {'callback': lambda x: x}
        with patch(
            'json.dump',
            side_effect=TypeError('Object not serializable'),
        ):
            with pytest.raises(
                ValueError,
                match='Failed to serialize',
            ):
                parser.save_metadata_json()

    def test_save_metadata_json_error(self, parser):
        """Test JSON file write error."""
        parser.metadata = {'filename': 'test.pdf'}
        with patch('builtins.open', side_effect=OSError('Permission denied')):
            with pytest.raises(OSError, match='Failed to save metadata JSON'):
                parser.save_metadata_json()


if __name__ == '__main__':
    pytest.main([__file__])
