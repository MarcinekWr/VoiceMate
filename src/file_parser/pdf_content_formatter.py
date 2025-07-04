"""
This module
contains the PDFContentFormatter
class for formatting extracted PDF content.
"""
from __future__ import annotations

import logging
from typing import Any

import fitz  # PyMuPDF

from src.utils.text_cleaner import TextCleaner


class PDFContentFormatter:
    """
    Formats extracted PDF data for various outputs.
    """

    def __init__(
        self,
        metadata: dict[str, Any],
        images: list[dict[str, Any]],
        tables: list[dict[str, Any]],
    ):
        """
        Initialize the PDFContentFormatter.
        """
        self.metadata = metadata
        self.images = images
        self.tables = tables
        self.structured_content: list[dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def create_structured_content(
        self,
        doc: fitz.Document,
    ) -> list[dict[str, Any]]:
        """Create a structured representation of all content by page."""
        try:
            if not isinstance(self.structured_content, list):
                self.structured_content = []

            for page_num in range(len(doc)):
                page_content = {
                    'page': page_num + 1,
                    'text': '',
                    'images': [],
                }

                try:
                    page = doc.load_page(page_num)
                    page_content['text'] = page.get_text()
                except RuntimeError as e:
                    self.logger.warning(
                        'Error getting text from page %s: %s', page_num, e,
                    )
                    page_content['text'] = ''

                for image in self.images:
                    if image['page'] == page_num + 1:
                        page_content['images'].append(image)

                self.structured_content.append(page_content)

        except (OSError, ValueError) as e:
            self.logger.error(
                'Unexpected error creating structured content: %s', e,
            )

        return self.structured_content

    def get_content_for_llm(self) -> str:
        """
        Get formatted content suitable for LLM processing.
        """
        if not self.structured_content:
            self.logger.warning(
                'No structured content available to format for LLM.',
            )
            return ''

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
                    cleaned_text = TextCleaner(page['text']).clean_text()
                    page_text += f'\nTEXT CONTENT:\n{cleaned_text}\n'
                except (OSError, ValueError) as e:
                    self.logger.warning(
                        'Error cleaning text for page %s: %s', page['page'], e,
                    )
                    page_text += f"\nTEXT CONTENT:\n{page['text']}\n"

            if page['images']:
                page_text += '\nIMAGES ON THIS PAGE:\n'
                for image in page['images']:
                    page_text += (
                        f"- Image {image['filename']} "
                        f"({image['width']}x{image['height']}, {image['size_kb']}KB)\n"
                    )
                    if image.get('description'):
                        page_text += f"  Description: {image['description']}\n"

            if self.tables:
                page_tables = [
                    table for table in self.tables if table['page'] == page['page']
                ]
                if page_tables:
                    page_text += '\nTABLES ON THIS PAGE:\n'
                    for table in page_tables:
                        page_text += f"  JSON Data: {table['json']}\n"

            llm_content.append(page_text)

        return '\n'.join(llm_content)
