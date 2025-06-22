"""PDF Parser class to parse PDF files and extract text,
images, and metadata with image descriptions."""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import fitz  # PyMuPDF
from dotenv import load_dotenv
from pdfminer.high_level import extract_text

from src.common.constants import LOG_FILE_PATH
from src.utils.extract_tables import extract_tables_from_pdf
from src.utils.text_cleaner import clean_text
from src.utils.image_describer import ImageDescriber

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOG_FILE_PATH,
    filemode="w",
)
logger = logging.getLogger(__name__)


class PdfParser:
    """
    A class to parse PDF files and extract text, images,
    and metadata with image descriptions.
    """

    def __init__(
        self,
        file_path: str,
        output_dir: str = "extracted_content",
        describe_images: bool = True,
        image_describer: Optional[ImageDescriber] = None,
    ):
        """
        Initialize the PDF parser.
        """
        self.file_path = file_path
        self.output_dir = output_dir
        self.describe_images = describe_images
        self.text = ""
        self.images: list[dict[str, Any]] = []
        self.tables: list[dict[str, Any]] = []
        self.structured_content: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}

        if self.describe_images:
            self.image_describer = image_describer or ImageDescriber()
        else:
            self.image_describer = None

        # Create output directory
        self._create_output_directory()

        logger.info("Initialized PdfParser with file: %s", file_path)

    def _create_output_directory(self) -> None:
        """Create the output directory if it doesn't exist."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create output directory {self.output_dir}: {e}")

    def parse_all(self) -> dict[str, Any]:
        """
        Parse all content from the PDF including text, images, tables, and metadata.
        """
        try:
            self.metadata = self.extract_metadata()
            self.text = self.extract_text()
            self.images = self.extract_images()
            self.tables = self.extract_tables()
            self.create_structured_content()

            logger.info("Successfully parsed all content from: %s", self.file_path)

            return {
                "text": self.text,
                "images": self.images,
                "tables": self.tables,
                "structured_content": self.structured_content,
                "metadata": self.metadata,
            }

        except (FileNotFoundError, ValueError) as e:
            logger.error("File error parsing PDF: %s", e)
            return {}
        except MemoryError as e:
            logger.error("Memory error parsing large PDF: %s", e)
            return {}
        except Exception as e:
            logger.error("Unexpected error parsing PDF %s: %s", self.file_path, e)
            return {}

    def extract_metadata(self) -> dict[str, Any]:
        """Extract basic metadata from PDF file."""
        metadata: dict[str, Any] = {}

        try:
            file_stats = os.stat(self.file_path)
            metadata["filename"] = os.path.basename(self.file_path)
            metadata["file_size_mb"] = round(file_stats.st_size / (1024 * 1024), 2)
            metadata["modified_time"] = datetime.fromtimestamp(
                file_stats.st_mtime
            ).isoformat()

        except OSError as e:
            logger.error("Error accessing file stats for %s: %s", self.file_path, e)
            metadata["error"] = f"Failed to get file stats: {str(e)}"
            return metadata

        try:
            doc = fitz.open(self.file_path)
            pdf_metadata = doc.metadata

            metadata["title"] = pdf_metadata.get("title", "")
            metadata["author"] = pdf_metadata.get("author", "")
            metadata["creation_date"] = pdf_metadata.get("creationDate", "")
            metadata["page_count"] = len(doc)

            doc.close()
            logger.info("Successfully extracted metadata")

        except fitz.FileDataError as e:
            logger.error("PDF file data error extracting metadata: %s", e)
            metadata["error"] = f"Invalid PDF file: {str(e)}"
        except Exception as e:
            logger.error("Unexpected error extracting metadata: %s", e)
            metadata["error"] = f"Unexpected error: {str(e)}"

        return metadata

    def extract_text(self) -> str:
        """Extract text content using pdfminer."""
        try:
            text = extract_text(self.file_path)
            logger.info("Text extraction completed")
            return text
        except FileNotFoundError as e:
            logger.error("File not found error extracting text: %s", e)
            return ""
        except Exception as e:
            logger.error("Unexpected error extracting text: %s", e)
            return ""

    def extract_images(self) -> list[dict[str, Any]]:
        """Extract images using PyMuPDF and describe them using ImageDescriber."""
        images_data: list[dict[str, Any]] = []

        try:
            doc = fitz.open(self.file_path)
        except fitz.FileDataError as e:
            logger.error("Cannot open PDF for image extraction: %s", e)
            return images_data

        try:
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    image_list = page.get_images()
                except fitz.FitzError as e:
                    logger.warning("Error loading page %s: %s", page_num, e)
                    continue

                for img_index, image in enumerate(image_list):
                    try:
                        xref = image[0]
                        pix = fitz.Pixmap(doc, xref)

                        # Skip very small images
                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue

                        # Get image data
                        image_data = pix.tobytes("png")
                        img_filename = f"image_p{page_num + 1}_{img_index + 1}.png"
                        img_path = os.path.join(self.output_dir, img_filename)
                        image_data_base64 = base64.b64encode(image_data).decode("utf-8")

                        # Save image to disk
                        try:
                            with open(img_path, "wb") as file:
                                file.write(image_data)
                        except OSError as e:
                            logger.warning(
                                "Failed to save image %s: %s", img_filename, e
                            )
                            pix = None
                            continue

                        # Get image description
                        description = self._get_image_description(img_path, image_data)

                        # Store image data
                        images_data.append(
                            {
                                "page": page_num + 1,
                                "filename": img_filename,
                                "base64": image_data_base64,
                                "path": img_path,
                                "width": pix.width,
                                "height": pix.height,
                                "size_kb": round(len(image_data) / 1024, 2),
                                "description": description,
                            }
                        )

                        pix = None

                    except fitz.FitzError as e:
                        logger.warning(
                            "Fitz error processing image %s on page %s: %s",
                            img_index,
                            page_num,
                            e,
                        )
                        continue
                    except Exception as e:
                        logger.warning(
                            "Unexpected error processing image %s on page %s: %s",
                            img_index,
                            page_num,
                            e,
                        )
                        continue

            doc.close()
            logger.info("Extracted %s images", len(images_data))

        except Exception as e:
            logger.error("Unexpected error during image extraction: %s", e)
            doc.close()

        return images_data

    def _get_image_description(self, img_path: str, image_data: bytes) -> str:
        """
        Get description for an image using the ImageDescriber.
        """
        if not self.describe_images or not self.image_describer:
            return "No description available"

        try:
            logger.info("Describing image: %s", os.path.basename(img_path))
            description = self.image_describer.describe_image(img_path)

            if (
                description.startswith("Error")
                or description == "Image description not available"
            ):
                description = self.image_describer.describe_image_from_bytes(image_data)

            return description

        except Exception as e:
            logger.error("Error getting image description: %s", e)
            return "Error generating description"

    def extract_tables(self) -> list[dict[str, Any]]:
        """Extract tables from the PDF file."""
        try:
            self.tables = extract_tables_from_pdf(self.file_path)
            logger.info("Extracted %s tables from PDF", len(self.tables))
            return self.tables
        except FileNotFoundError as e:
            logger.error("File not found for table extraction: %s", e)
            self.tables = []
            return []
        except Exception as e:
            logger.error("Unexpected error extracting tables: %s", e)
            self.tables = []
            return []

    def create_structured_content(self) -> None:
        """Create a structured representation of all content by page."""
        try:
            doc = fitz.open(self.file_path)
        except fitz.FileDataError as e:
            logger.error("Cannot open PDF for structured content: %s", e)
            return

        try:
            for page_num in range(len(doc)):
                page_content = {
                    "page": page_num + 1,
                    "text": "",
                    "images": [],
                }

                try:
                    page = doc.load_page(page_num)
                    page_content["text"] = page.get_text()
                except fitz.FitzError as e:
                    logger.warning("Error getting text from page %s: %s", page_num, e)
                    page_content["text"] = ""

                # Add images for this page
                for image in self.images:
                    if image["page"] == page_num + 1:
                        page_content["images"].append(image)

                self.structured_content.append(page_content)

            doc.close()

        except Exception as e:
            logger.error("Unexpected error creating structured content: %s", e)
            doc.close()

    def clean_data(self) -> str:
        """Clean the extracted text data."""
        if not self.text:
            logger.warning("No text to clean. Have you called parse_all()?")
            return ""
        try:
            self.text = clean_text(self.text)
            return clean_text(self.text)
        except Exception as e:
            logger.error("Error cleaning text data: %s", e)
            return self.text

    def get_content_for_llm(self) -> str:
        """
        Get formatted content suitable for LLM processing.
        Includes text, image descriptions, and table data organized by page.
        """
        if not self.structured_content:
            return self.clean_data()

        llm_content = []

        if self.metadata:
            llm_content.append("--- DOCUMENT METADATA ---")
            llm_content.append(f"Filename: {self.metadata.get('filename', 'N/A')}")
            llm_content.append(
                f"File Size: {self.metadata.get('file_size_mb', 'N/A')} MB"
            )
            llm_content.append(f"Pages: {self.metadata.get('page_count', 'N/A')}")
            llm_content.append("")

        for page in self.structured_content:
            page_text = f"\n--- PAGE {page['page']} ---\n"

            if page["text"].strip():
                try:
                    cleaned_text = clean_text(page["text"])
                    page_text += f"\nTEXT CONTENT:\n{cleaned_text}\n"
                except Exception as e:
                    logger.warning(
                        "Error cleaning text for page %s: %s", page["page"], e
                    )
                    page_text += f"\nTEXT CONTENT:\n{page['text']}\n"

            if page["images"]:
                page_text += "\nIMAGES ON THIS PAGE:\n"
                for image in page["images"]:
                    page_text += (
                        f"- Image {image['filename']} "
                        f"({image['width']}x{image['height']}, {image['size_kb']}KB)\n"
                    )
                    if image.get("description"):
                        page_text += f"  Description: {image['description']}\n"

            if hasattr(self, "tables") and self.tables:
                page_tables = [
                    table for table in self.tables if table["page"] == page["page"]
                ]
                if page_tables:
                    page_text += "\nTABLES ON THIS PAGE:\n"
                    for table in page_tables:
                        page_text += f"  JSON Data: {table['json']}\n"

            llm_content.append(page_text)

        return "\n".join(llm_content)

    def save_summary_report(self) -> str:
        """Save a simplified summary report of extracted content."""
        report_path = os.path.join(self.output_dir, "extraction_report.txt")

        try:
            with open(report_path, "w", encoding="utf-8") as file:
                file.write("PDF CONTENT EXTRACTION REPORT\n")
                file.write("=" * 50 + "\n\n")
                file.write(f"Source File: {self.file_path}\n")
                file.write(f"Total Pages: {len(self.structured_content)}\n")
                file.write(f"Images Extracted: {len(self.images)}\n")
                file.write(f"Text Length: {len(self.text)} characters\n")

                file.write("\n")

                if self.metadata:
                    file.write("METADATA\n")
                    file.write("-" * 20 + "\n")
                    file.write(f"Filename: {self.metadata.get('filename', 'N/A')}\n")
                    file.write(
                        f"File Size: {self.metadata.get('file_size_mb', 'N/A')} MB\n"
                    )
                    file.write(f"Pages: {self.metadata.get('page_count', 'N/A')}\n")
                    file.write(
                        f"Modified: {self.metadata.get('modified_time', 'N/A')}\n"
                    )

                    if self.metadata.get("title"):
                        file.write(f"Title: {self.metadata['title']}\n")
                    if self.metadata.get("author"):
                        file.write(f"Author: {self.metadata['author']}\n")
                    if self.metadata.get("creation_date"):
                        file.write(f"Created: {self.metadata['creation_date']}\n")
                    file.write("\n")

                file.write("PAGE SUMMARY\n")
                file.write("-" * 20 + "\n")
                for page in self.structured_content:
                    file.write(f"Page {page['page']}:\n")
                    file.write(f"  - Text: {len(page['text'])} characters\n")
                    file.write(f"  - Images: {len(page['images'])}\n")

                    if page["images"]:
                        for image in page["images"]:
                            file.write(
                                f"    * {image['filename']} "
                                f"({image['width']}x{image['height']})\n"
                            )
                            if image.get("description"):
                                file.write(
                                    f"      Description: {image['description'][:100]}...\n"
                                )
                    file.write("\n")

        except OSError as e:
            logger.error("Error saving summary report: %s", e)
            raise OSError(f"Failed to save summary report: {e}")

        return report_path

    def save_metadata_json(self) -> str:
        """Save metadata as JSON file for programmatic access."""
        metadata_path = os.path.join(self.output_dir, "metadata.json")

        try:
            # Include image describer status in metadata
            extended_metadata = self.metadata.copy()

            with open(metadata_path, "w", encoding="utf-8") as file:
                json.dump(
                    extended_metadata,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
        except OSError as e:
            logger.error("Error saving metadata JSON: %s", e)
            raise OSError(f"Failed to save metadata JSON: {e}")
        except (TypeError, ValueError) as e:
            logger.error("JSON serialization error: %s", e)
            raise ValueError(f"Failed to serialize metadata to JSON: {e}")

        return metadata_path

    def initiate(self) -> str:
        """Initiate the parsing process and return content formatted for LLM processing."""
        self.parse_all()
        self.save_summary_report()
        self.save_metadata_json()
        return self.get_content_for_llm()
