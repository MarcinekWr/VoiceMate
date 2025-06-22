"""PDF Parser class to parse PDF files and extract text,
images, and metadata with image descriptions."""
from __future__ import annotations

import base64
import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pdfminer.high_level import extract_text
from PIL import Image

from src.common.CONSTANTS import LOG_FILE_PATH
from src.utils.extract_tables import extract_tables_from_pdf
from src.utils.text_cleaner import clean_text

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=LOG_FILE_PATH,
    filemode='w',
)
logger = logging.getLogger(__name__)


class PdfParser:
    """
    A class to parse files and extract text, images,
    and metadata with image descriptions.
    """

    def __init__(
        self,
        file_path: str,
        output_dir: str = 'extracted_content',
        describe_images: bool = True,
    ):
        self.file_path = file_path
        self.output_dir = output_dir
        self.describe_images = describe_images
        self.text = ''
        self.images: list[dict[str, Any]] = []
        self.tables: list[dict[str, Any]] = []
        self.structured_content: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}
        self.llm = None
        self.prompt_template = None

        if self.describe_images:
            self.setup_image_describer()

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise OSError(
                f'Failed to create output directory {output_dir}: {e}',
            )

        logger.info('Initialized PdfParser with file: %s', file_path)

    def setup_image_describer(self):
        """Set up the image description LLM."""
        try:
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('API_VERSION'),
                deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
                model_name=os.getenv('AZURE_OPENAI_MODEL'),
            )

            prompt_path = 'src/prompts/image_describer.txt'
            try:
                if os.path.exists(prompt_path):
                    prompt_text = Path(prompt_path).read_text(
                        encoding='utf-8',
                    )
                    self.prompt_template = PromptTemplate.from_template(
                        prompt_text,
                    )
                else:
                    self.prompt_template = PromptTemplate.from_template(
                        'Describe this image in detail. Focus on text, '
                        'charts, diagrams, and any important visual elements.',
                    )
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(
                    'Failed to load custom prompt, using default: %s',
                    e,
                )
                self.prompt_template = PromptTemplate.from_template(
                    'Describe this image in detail. Focus on text, '
                    'charts, diagrams, and any important visual elements.',
                )

            logger.info('Image describer setup completed')
        except ImportError as e:
            logger.warning(
                'Import error setting up image describer: '
                '%s. Check if langchain_openai is installed.',
                e,
            )
            self.describe_images = False
        except Exception as e:
            logger.warning(
                'Unexpected error setting up image describer: %s. '
                'Images will be extracted without descriptions.',
                e,
            )
            self.describe_images = False

    def describe_image(self, image_path: str) -> str:
        """Describe an image using the LLM."""
        if (
            not self.describe_images
            or not self.llm
                or not self.prompt_template
        ):
            return 'Image description not available'

        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(
                    f'Image file not found: {image_path}',
                )

            with Image.open(image_path) as image:
                buffered = io.BytesIO()
                image.save(buffered, format='PNG')
                image_base64 = base64.b64encode(
                    buffered.getvalue(),
                ).decode('utf-8')

            prompt_text = self.prompt_template.format()
            message = [
                {'type': 'text', 'text': prompt_text},
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/png;base64,{image_base64}',
                    },
                },
            ]

            response = self.llm.invoke([HumanMessage(content=message)])
            return response.content
        except FileNotFoundError as e:
            logger.error('Image file not found: %s', e)
            return 'Image description not available'
        except Exception as e:
            logger.error(
                'Unexpected error describing image %s: %s',
                image_path,
                e,
            )
            return f'Error generating description: {str(e)}'

    def parse_all(self) -> dict[str, Any]:
        """
        Modified version of parse_all() to include table extraction
        and image descriptions.
        """
        try:
            self.metadata = self.extract_metadata()
            self.text = self.extract_text()
            self.images = self.extract_images()
            self.tables = self.extract_tables()
            self.create_structured_content()

            logger.info(
                'Successfully parsed all content from: %s',
                self.file_path,
            )

            return {
                'text': self.text,
                'images': self.images,
                'tables': self.tables,
                'structured_content': self.structured_content,
                'metadata': self.metadata,
            }

        except (FileNotFoundError, ValueError) as e:
            logger.error('File error parsing PDF: %s', e)
            return {}
        except MemoryError as e:
            logger.error('Memory error parsing large PDF: %s', e)
            return {}
        except Exception as e:
            logger.error(
                'Unexpected error parsing PDF %s: %s',
                self.file_path,
                e,
            )
            return {}

    def extract_metadata(self) -> dict[str, Any]:
        """Extract basic metadata from PDF file."""
        metadata: dict[str, Any] = {}

        try:
            file_stats = os.stat(self.file_path)
            metadata['filename'] = os.path.basename(self.file_path)
            metadata['file_size_mb'] = round(
                file_stats.st_size / (1024 * 1024),
                2,
            )
            metadata['modified_time'] = datetime.fromtimestamp(
                file_stats.st_mtime,
            ).isoformat()

        except OSError as e:
            logger.error(
                'Error accessing file stats for %s: %s',
                self.file_path,
                e,
            )
            metadata['error'] = f'Failed to get file stats: {str(e)}'
            return metadata

        try:
            doc = fitz.open(self.file_path)
            pdf_metadata = doc.metadata

            metadata['title'] = pdf_metadata.get('title', '')
            metadata['author'] = pdf_metadata.get('author', '')
            metadata['creation_date'] = pdf_metadata.get('creationDate', '')
            metadata['page_count'] = len(doc)

            doc.close()
            logger.info('Successfully extracted metadata')

        except fitz.FileDataError as e:
            logger.error('PDF file data error extracting metadata: %s', e)
            metadata['error'] = f'Invalid PDF file: {str(e)}'
        except Exception as e:
            logger.error('Unexpected error extracting metadata: %s', e)
            metadata['error'] = f'Unexpected error: {str(e)}'

        return metadata

    def extract_text(self) -> str:
        """Extract text content using pdfminer."""
        try:
            text = extract_text(self.file_path)
            logger.info('Text extraction completed')
            return text
        except FileNotFoundError as e:
            logger.error('File not found error extracting text: %s', e)
            return ''
        except Exception as e:
            logger.error('Unexpected error extracting text: %s', e)
            return ''

    def extract_images(self) -> list[dict[str, Any]]:
        """Extract images using PyMuPDF and describe them."""
        images_data: list[dict[str, Any]] = []

        try:
            doc = fitz.open(self.file_path)
        except fitz.FileDataError as e:
            logger.error('Cannot open PDF for image extraction: %s', e)
            return images_data

        try:
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    image_list = page.get_images()
                except fitz.FitzError as e:
                    logger.warning('Error loading page %s: %s', page_num, e)
                    continue

                for img_index, image in enumerate(image_list):
                    try:
                        xref = image[0]
                        pix = fitz.Pixmap(doc, xref)

                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue

                        image_data = pix.tobytes('png')
                        img_filename = (
                            f'image_p{page_num + 1}_{img_index + 1}.png'
                        )
                        img_path = os.path.join(
                            self.output_dir,
                            img_filename,
                        )
                        image_data_base64 = base64.b64encode(
                            pix.tobytes('png'),
                        ).decode('utf-8')

                        try:
                            with open(img_path, 'wb') as file:
                                file.write(image_data)
                        except OSError as e:
                            logger.warning(
                                'Failed to save image %s: %s',
                                img_filename,
                                e,
                            )
                            pix = None
                            continue

                        description = 'No description available'
                        if self.describe_images:
                            logger.info(
                                'Describing image: %s',
                                img_filename,
                            )
                            description = self.describe_image(img_path)

                        images_data.append(
                            {
                                'page': page_num + 1,
                                'filename': img_filename,
                                'base64': image_data_base64,
                                'path': img_path,
                                'width': pix.width,
                                'height': pix.height,
                                'size_kb': round(len(image_data) / 1024, 2),
                                'description': description,
                            },
                        )

                        pix = None

                    except fitz.FitzError as e:
                        logger.warning(
                            'Fitz error processing '
                            'image %s on page %s: %s',
                            img_index,
                            page_num,
                            e,
                        )
                        continue
                    except Exception as e:
                        logger.warning(
                            'Unexpected '
                            'error processing image %s '
                            'on page %s: %s',
                            img_index,
                            page_num,
                            e,
                        )
                        continue

            doc.close()
            logger.info('Extracted %s images', len(images_data))

        except Exception as e:
            logger.error('Unexpected error during image extraction: %s', e)
            doc.close()

        return images_data

    def extract_tables(self) -> list[dict[str, Any]]:
        """Extract tables from the PDF file."""
        try:
            self.tables = extract_tables_from_pdf(self.file_path)
            logger.info('Extracted %s tables from PDF', len(self.tables))
            return self.tables
        except FileNotFoundError as e:
            logger.error('File not found for table extraction: %s', e)
            self.tables = []
            return []
        except Exception as e:
            logger.error('Unexpected error extracting tables: %s', e)
            self.tables = []
            return []

    def create_structured_content(self):
        """Create a structured representation of all content by page."""
        try:
            doc = fitz.open(self.file_path)
        except fitz.FileDataError as e:
            logger.error('Cannot open PDF for structured content: %s', e)
            return

        try:
            for page_num in range(len(doc)):
                page_content = {
                    'page': page_num + 1,
                    'text': '',
                    'images': [],
                }

                try:
                    page = doc.load_page(page_num)
                    page_content['text'] = page.get_text()
                except fitz.FitzError as e:
                    logger.warning(
                        'Error getting text from page %s: %s',
                        page_num,
                        e,
                    )
                    page_content['text'] = ''

                for image in self.images:
                    if image['page'] == page_num + 1:
                        page_content['images'].append(image)

                self.structured_content.append(page_content)

            doc.close()

        except Exception as e:
            logger.error(
                'Unexpected error creating structured content: %s',
                e,
            )
            doc.close()

    def clean_data(self) -> str:
        """Clean the extracted text data."""
        if not self.text:
            logger.warning('No text to clean. Have you called parse_all()?')
            return ''
        try:
            self.text = clean_text(self.text)
            return clean_text(self.text)
        except Exception as e:
            logger.error('Error cleaning text data: %s', e)
            return self.text

    def get_content_for_llm(self) -> str:
        """
        Modified version to include tables and image descriptions
        in LLM content per page.
        """
        if not self.structured_content:
            return self.clean_data()

        llm_content = []

        if self.metadata:
            llm_content.append('--- DOCUMENT METADATA ---')
            llm_content.append(
                f"Filename: {self.metadata.get('filename', 'N/A')}",
            )
            llm_content.append(
                f"File Size: {self.metadata.get('file_size_mb', 'N/A')} MB",
            )
            llm_content.append(
                f"Pages: {self.metadata.get('page_count', 'N/A')}",
            )
            llm_content.append('')

        for page in self.structured_content:
            page_text = f"\n--- PAGE {page['page']} ---\n"

            if page['text'].strip():
                try:
                    cleaned_text = clean_text(page['text'])
                    page_text += f'\nTEXT CONTENT:\n{cleaned_text}\n'
                except Exception as e:
                    logger.warning(
                        'Error cleaning text for page %s: %s',
                        page['page'],
                        e,
                    )
                    page_text += f"\nTEXT CONTENT:\n{page['text']}\n"

            if page['images']:
                page_text += '\nIMAGES ON THIS PAGE:\n'
                for image in page['images']:
                    page_text += (
                        f"- Image {image['filename']}"
                        f"({image['width']}x{image['height']}, "
                        f"{image['size_kb']}KB)\n"
                    )
                    if image.get('description'):
                        page_text += f"  Description: {image['description']}\n"

            if hasattr(self, 'tables') and self.tables:
                page_tables = [
                    table for table in self.tables
                    if table['page'] == page['page']
                ]
                if page_tables:
                    page_text += '\nTABLES ON THIS PAGE:\n'
                    for table in page_tables:
                        page_text += f"  JSON Data: {table['json']}\n"

            llm_content.append(page_text)

        return '\n'.join(llm_content)

    def save_summary_report(self) -> str:
        """Save a simplified summary report of extracted content."""
        report_path = os.path.join(self.output_dir, 'extraction_report.txt')

        try:
            with open(report_path, 'w', encoding='utf-8') as file:
                file.write('PDF CONTENT EXTRACTION REPORT\n')
                file.write('=' * 50 + '\n\n')
                file.write(f'Source File: {self.file_path}\n')
                file.write(f'Total Pages: {len(self.structured_content)}\n')
                file.write(f'Images Extracted: {len(self.images)}\n')
                file.write(f'Text Length: {len(self.text)} characters\n\n')

                if self.metadata:
                    file.write('METADATA\n')
                    file.write('-' * 20 + '\n')
                    file.write(
                        f"Filename: {self.metadata.get('filename', 'N/A')}\n",
                    )
                    file.write(
                        (
                            'File Size: %s MB\n' %
                            self.metadata.get('file_size_mb', 'N/A')
                        ),
                    )
                    file.write(
                        f"Pages: {self.metadata.get('page_count', 'N/A')}\n",
                    )
                    file.write(
                        (
                            'Modified: %s \n' %
                            self.metadata.get('modified_time', 'N/A')
                        ),
                    )

                    if self.metadata.get('title'):
                        file.write(f"Title: {self.metadata['title']}\n")
                    if self.metadata.get('author'):
                        file.write(f"Author: {self.metadata['author']}\n")
                    if self.metadata.get('creation_date'):
                        file.write(
                            f"Created: {self.metadata['creation_date']}\n",
                        )
                    file.write('\n')

                file.write('PAGE SUMMARY\n')
                file.write('-' * 20 + '\n')
                for page in self.structured_content:
                    file.write(f"Page {page['page']}:\n")
                    file.write(f"  - Text: {len(page['text'])} characters\n")
                    file.write(f"  - Images: {len(page['images'])}\n")
                    if page['images']:
                        for image in page['images']:
                            file.write(
                                f"    * {image['filename']} "
                                f"({image['width']}x{image['height']})\n",
                            )
                            if image.get('description'):
                                file.write(
                                    f'      Description: '
                                    f"{image['description'][:100]}...\n",
                                )
                    file.write('\n')

        except OSError as e:
            logger.error('Error saving summary report: %s', e)
            raise OSError(f'Failed to save summary report: {e}')

        return report_path

    def save_metadata_json(self) -> str:
        """Save metadata as JSON file for programmatic access."""
        metadata_path = os.path.join(self.output_dir, 'metadata.json')

        try:
            with open(metadata_path, 'w', encoding='utf-8') as file:
                json.dump(
                    self.metadata,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
        except OSError as e:
            logger.error('Error saving metadata JSON: %s', e)
            raise OSError(f'Failed to save metadata JSON: {e}')
        except (TypeError, ValueError) as e:
            logger.error('JSON serialization error: %s', e)
            raise ValueError(f'Failed to serialize metadata to JSON: {e}')

        return metadata_path

    def initiate(self) -> str:
        self.parse_all()
        self.save_summary_report()
        self.save_metadata_json()
        return self.get_content_for_llm()
