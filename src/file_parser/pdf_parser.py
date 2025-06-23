"""PDF Parser class to parse PDF files and extract text,
images, and metadata with image descriptions."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional

import fitz  # PyMuPDF
from dotenv import load_dotenv
from pdfminer.high_level import extract_text

from src.common.constants import LOG_FILE_PATH
from src.utils.extract_tables import PDFTableParser
from src.utils.image_describer import ImageDescriber
from src.file_parser.pdf_image_extractor import PDFImageExtractor
from src.utils.logging_config import setup_logger
from src.file_parser.pdf_content_formatter import PDFContentFormatter

load_dotenv()


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
        self.logger = setup_logger(LOG_FILE_PATH)
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

        self.table_parser = PDFTableParser(self.file_path)
        self.image_extractor = PDFImageExtractor(
            output_dir=self.output_dir,
            image_describer=self.image_describer,
            describe_images=self.describe_images,
        )
        self.create_output_directory()

        self.logger.info("Initialized PdfParser with file: %s", file_path)

    def create_output_directory(self) -> None:
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
            doc = fitz.open(self.file_path)
            self.metadata = self.extract_metadata(doc)
            self.text = self.extract_text()
            self.images = self.image_extractor.extract_images(doc)
            self.tables = self.table_parser.extract_tables()

            formatter = PDFContentFormatter(
                metadata=self.metadata,
                images=self.images,
                tables=self.tables,
            )
            self.structured_content = formatter.create_structured_content(doc)

            self.logger.info("Successfully parsed all content from: %s", self.file_path)

            return {
                "text": self.text,
                "images": self.images,
                "tables": self.tables,
                "structured_content": self.structured_content,
                "metadata": self.metadata,
            }

        except (FileNotFoundError, ValueError) as e:
            self.logger.error("File error parsing PDF: %s", e)
            return {}
        except MemoryError as e:
            self.logger.error("Memory error parsing large PDF: %s", e)
            return {}
        except Exception as e:
            self.logger.error("Unexpected error parsing PDF %s: %s", self.file_path, e)
            return {}
        finally:
            if "doc" in locals() and doc:
                doc.close()

    def extract_metadata(self, doc: fitz.Document) -> dict[str, Any]:
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
            self.logger.error(
                "Error accessing file stats for %s: %s", self.file_path, e
            )
            metadata["error"] = f"Failed to get file stats: {str(e)}"
            return metadata

        try:
            pdf_metadata = doc.metadata

            metadata["title"] = pdf_metadata.get("title", "")
            metadata["author"] = pdf_metadata.get("author", "")
            metadata["creation_date"] = pdf_metadata.get("creationDate", "")
            metadata["page_count"] = len(doc)

            self.logger.info("Successfully extracted metadata")

        except RuntimeError as e:
            self.logger.error("PDF file data error extracting metadata: %s", e)
            metadata["error"] = f"Invalid PDF file: {str(e)}"
        except Exception as e:
            self.logger.error("Unexpected error extracting metadata: %s", e)
            metadata["error"] = f"Unexpected error: {str(e)}"

        return metadata

    def extract_text(self) -> str:
        """Extract text content using pdfminer."""
        try:
            text = extract_text(self.file_path)
            self.logger.info("Text extraction completed")
            return text
        except FileNotFoundError as e:
            self.logger.error("File not found error extracting text: %s", e)
            return ""
        except Exception as e:
            self.logger.error("Unexpected error extracting text: %s", e)
            return ""

    def get_content_for_llm(self) -> str:
        """
        Get formatted content suitable for LLM processing.
        """
        formatter = PDFContentFormatter(
            metadata=self.metadata,
            images=self.images,
            tables=self.tables,
        )
        formatter.structured_content = self.structured_content
        return formatter.get_content_for_llm()

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
            self.logger.error("Error saving summary report: %s", e)
            raise OSError(f"Failed to save summary report: {e}")

        return report_path

    def save_metadata_json(self) -> str:
        """Save metadata as JSON file for programmatic access."""
        metadata_path = os.path.join(self.output_dir, "metadata.json")

        try:
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
            self.logger.error("Error saving metadata JSON: %s", e)
            raise OSError(f"Failed to save metadata JSON: {e}")
        except (TypeError, ValueError) as e:
            self.logger.error("JSON serialization error: %s", e)
            raise ValueError(f"Failed to serialize metadata to JSON: {e}")

        return metadata_path

    def save_llm_content(self, content: str) -> str:
        """Saves the LLM-ready content to a text file."""
        report_path = os.path.join(self.output_dir, "llm_content.txt")
        try:
            with open(report_path, "w", encoding="utf-8") as file:
                file.write(content)
            self.logger.info(f"LLM-ready content saved to {report_path}")
        except OSError as e:
            self.logger.error(f"Error saving LLM content report: {e}")
            raise OSError(f"Failed to save LLM content report: {e}")
        return report_path

    def initiate(self) -> str:
        """Initiate the parsing process and return content formatted for LLM processing."""
        self.parse_all()
        self.save_summary_report()
        self.save_metadata_json()
        llm_content = self.get_content_for_llm()
        self.save_llm_content(llm_content)
        return llm_content
