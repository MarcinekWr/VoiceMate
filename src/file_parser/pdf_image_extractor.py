"""
This module contains the PDFImageExtractor
class for extracting images from PDF files.
"""
from __future__ import annotations

import base64
import os
from typing import Any

import fitz  # PyMuPDF

from src.utils.image_describer import ImageDescriber
from src.utils.logging_config import get_request_id, get_session_logger


class PDFImageExtractor:
    """
    Extracts and processes images from a PDF document.
    """

    def __init__(
        self,
        output_dir: str,
        image_describer: ImageDescriber | None = None,
        describe_images: bool = True,
        request_id=None,
    ):
        """
        Initialize the PDFImageExtractor.
        """
        self.output_dir = output_dir
        self.image_describer = image_describer
        self.describe_images = describe_images
        self.request_id = request_id or get_request_id()
        self.logger = get_session_logger(self.request_id)

    def extract_images(
        self,
        doc: fitz.Document,
    ) -> list[dict[str, Any]]:
        """Extract images
        using PyMuPDF and describe them using ImageDescriber."""
        images_data: list[dict[str, Any]] = []

        try:
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    image_list = page.get_images(full=True)
                except RuntimeError as e:
                    self.logger.warning(
                        'Error loading page %s: %s',
                        page_num,
                        e,
                    )
                    continue

                for img_index, image in enumerate(image_list):
                    try:
                        xref = image[0]
                        pix = fitz.Pixmap(doc, xref)

                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue

                        image_data = pix.tobytes('png')
                        img_filename = f'image_p{page_num + 1}_{img_index + 1}.png'
                        img_path = os.path.join(self.output_dir, img_filename)
                        image_data_base64 = base64.b64encode(
                            image_data,
                        ).decode('utf-8')

                        try:
                            with open(img_path, 'wb') as file:
                                file.write(image_data)
                        except OSError as e:
                            self.logger.warning(
                                'Failed to save image %s: %s', img_filename, e,
                            )
                            pix = None
                            continue

                        # Get image description
                        description = self._get_image_description(
                            img_path, image_data,
                        )

                        # Store image data
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

                    except RuntimeError as e:
                        self.logger.warning(
                            'Fitz error processing image %s on page %s: %s',
                            img_index,
                            page_num,
                            e,
                        )
                        continue
                    except (OSError, ValueError) as e:
                        self.logger.warning(
                            'Unexpected error processing image %s on page %s: %s',
                            img_index,
                            page_num,
                            e,
                        )
                        continue

            self.logger.info('Extracted %s images', len(images_data))

        except (OSError, ValueError) as e:
            self.logger.error(
                'Unexpected error during image extraction: %s', e,
            )

        return images_data

    def _get_image_description(self, img_path: str, image_data: bytes) -> str:
        """
        Get description for an image using the ImageDescriber.
        """
        if not self.describe_images or not self.image_describer:
            return 'No description available'

        try:
            self.logger.info(
                'Describing image: %s',
                os.path.basename(img_path),
            )
            description = self.image_describer.describe_image(img_path)

            if (
                description.startswith('Error')
                or description == 'Image description not available'
            ):
                description = self.image_describer.describe_image_from_bytes(
                    image_data,
                )

            return description

        except (OSError, AttributeError, ValueError) as e:
            self.logger.error('Error getting image description: %s', e)
            return 'Error generating description'
