from __future__ import annotations

import gc
import mimetypes
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import markdown
import pdfkit
import requests
from PIL import Image
from pptx import Presentation
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import QEventLoop, QTimer, QUrl
from PyQt5.QtGui import QPageLayout, QPageSize
from PyQt5.QtWidgets import QApplication
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from common.constants import LOG_FILE_PATH
from file_parser import pdf_parser
from utils.logging_config import setup_logger
import logging

class FileConverter:
    SUPPORTED_FORMATS = {
        "images": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"],
        "web": [".html", ".htm"],
        "presentations": [".pptx"],
        "markdown": [".md", ".markdown"],
        "pdf": [".pdf"],
    }

    def __init__(self, file_path: str, output_dir: str = "assets"):
        """Initialize the FileConverter with a file path and output directory."""
        self.file_path = file_path
        self.output_dir = output_dir
        self.temp_files: list[str] = []
        self.logger = logging.getLogger(__name__)

        self.create_output_dir()
        self.logger.info(f"FileConverter initialized for: {file_path}")

    def create_output_dir(self) -> None:
        """Create the output directory if it doesn't exist."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            self.logger.error(
                f"Failed to create output directory {self.output_dir}: {e}"
            )
            raise

    def detect_file_type(self) -> str:
        """Detect the type of file based on its extension or MIME type."""
        if not os.path.exists(self.file_path):
            self.logger.error(f"File does not exist: {self.file_path}")
            raise FileNotFoundError(f"File does not exist: {self.file_path}")

        file_ext = Path(self.file_path).suffix.lower()
        self.logger.debug(f"Detected file extension: {file_ext}")

        for file_type, extensions in self.SUPPORTED_FORMATS.items():
            if file_ext in extensions:
                self.logger.info(f"File type detected: {file_type}")
                return file_type

        mime_type, _ = mimetypes.guess_type(self.file_path)
        if mime_type:
            self.logger.debug(f"MIME type detected: {mime_type}")
            if mime_type.startswith("image/"):
                self.logger.info("File type detected: images (via MIME)")
                return "images"
            elif mime_type == "application/pdf":
                self.logger.info("File type detected: pdf (via MIME)")
                return "pdf"

        self.logger.warning(f"Unknown file type for: {self.file_path}")
        return "unknown"

    def _generate_unique_filename(self, base_name: str, extension: str) -> str:
        """Generate a unique filename in the output directory."""
        output_path = os.path.join(self.output_dir, f"{base_name}{extension}")

        if os.path.exists(output_path):
            timestamp = int(time.time())
            output_path = os.path.join(
                self.output_dir,
                f"{base_name}_{timestamp}{extension}",
            )
            self.logger.debug(f"Generated unique filename: {output_path}")

        return output_path

    def convert_image_to_pdf(self) -> str:
        """Convert image file to PDF format."""
        self.logger.info(f"Converting image to PDF: {self.file_path}")
        original_name = Path(self.file_path).stem
        output_path = self._generate_unique_filename(original_name, ".pdf")

        try:
            with Image.open(self.file_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                    self.logger.debug("Image converted to RGB mode")
                img.save(output_path, "PDF", resolution=100.0)
            self.logger.info(f"Image successfully converted to PDF: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Image conversion failed: {str(e)}")
            raise Exception(f"Image conversion error: {str(e)}")

    def is_valid_url(self, url: str) -> bool:
        """Validate if the provided string is a valid URL."""
        try:
            result = urlparse(url)
            is_valid = all([result.scheme, result.netloc])
            self.logger.debug(f"URL validation for {url}: {is_valid}")
            return is_valid
        except Exception as e:
            self.logger.debug(f"URL validation failed for {url}: {str(e)}")
            return False

    def get_domain_name(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            domain = urlparse(url).netloc
            clean_domain = (
                domain.replace("www.", "")
                .replace(
                    ".",
                    "_",
                )
                .replace("-", "_")[:30]
            )
            self.logger.debug(f"Extracted domain name: {clean_domain}")
            return clean_domain
        except Exception as e:
            self.logger.warning(f"Could not extract domain from {url}: {str(e)}")
            return "website"

    def convert_url_to_pdf(self) -> str:
        """Convert URL to PDF format."""
        self.logger.info(f"Converting URL to PDF: {self.file_path}")

        if not self.is_valid_url(self.file_path):
            self.logger.error(f"Invalid URL: {self.file_path}")
            raise ValueError(f"Invalid URL: {self.file_path}")

        try:
            self.logger.debug("Checking URL accessibility...")
            response = requests.get(
                self.file_path,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0",
                },
            )
            if response.status_code >= 400:
                self.logger.error(
                    f"URL returned status code {response.status_code}",
                )
                raise Exception(
                    f"Unavailable page (code: {response.status_code})",
                )
        except requests.RequestException as e:
            self.logger.error(
                f"Connection error for URL {self.file_path}: {str(e)}",
            )
            raise Exception(f"Connection error: {str(e)}")

        domain_name = self.get_domain_name(self.file_path)
        output_path = self._generate_unique_filename(domain_name, ".pdf")

        # Create QApplication if not exists
        app = QApplication.instance() or QApplication(sys.argv)
        self.logger.debug("Initializing web engine for PDF conversion...")

        web_view = QtWebEngineWidgets.QWebEngineView()
        web_view.setZoomFactor(1)

        # Setup page layout
        layout = QPageLayout()
        layout.setPageSize(QPageSize(QPageSize.A4))
        layout.setOrientation(QPageLayout.Portrait)

        # Create event loop for synchronization
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)

        def handle_load_finished(ok):
            if not ok:
                self.logger.error(f"Failed to load web page: {self.file_path}")
                loop.quit()
                raise Exception(f"Failed to load page: {self.file_path}")
            self.logger.debug("Web page loaded successfully, generating PDF...")
            web_view.page().printToPdf(output_path, layout)

        def handle_pdf_finished(path, success):
            loop.quit()
            if not success:
                self.logger.error(f"PDF creation failed for: {self.file_path}")
                raise Exception(f"PDF creation failed for: {self.file_path}")
            self.logger.debug("PDF generation completed successfully")

        web_view.loadFinished.connect(handle_load_finished)
        web_view.page().pdfPrintingFinished.connect(handle_pdf_finished)

        web_view.load(QUrl(self.file_path))

        timer.start(30000)
        loop.exec_()

        # Cleanup Qt resources
        web_view.page().deleteLater()
        web_view.deleteLater()

        # Cleanup if we created the application
        if QApplication.instance() is None:
            app.quit()

        # Force garbage collection
        gc.collect()

        if not os.path.exists(output_path):
            self.logger.error(f"PDF file was not created: {output_path}")
            raise Exception(f"PDF not created for: {self.file_path}")

        self.logger.info(f"URL successfully converted to PDF: {output_path}")
        return output_path

    def convert_html_to_pdf(self) -> str:
        """Convert HTML file to PDF format."""
        self.logger.info(f"Converting HTML to PDF: {self.file_path}")
        original_name = Path(self.file_path).stem
        output_path = self._generate_unique_filename(original_name, ".pdf")

        try:
            pdfkit.from_file(
                self.file_path,
                output_path,
                options={"quiet": ""},
            )
            self.logger.info(f"HTML successfully converted to PDF: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"HTML conversion failed: {str(e)}")
            raise Exception(f"HTML conversion error: {str(e)}")

    def convert_markdown_to_pdf(self) -> str:
        """Convert Markdown file to PDF format."""
        self.logger.info(f"Converting Markdown to PDF: {self.file_path}")
        original_name = Path(self.file_path).stem
        output_path = self._generate_unique_filename(original_name, ".pdf")

        try:
            with open(self.file_path, encoding="utf-8") as f:
                html = markdown.markdown(f.read())
            pdfkit.from_string(html, output_path, options={"quiet": ""})
            self.logger.info(
                f"Markdown successfully converted to PDF: {output_path}",
            )
            return output_path
        except Exception as e:
            self.logger.error(f"Markdown conversion failed: {str(e)}")
            raise Exception(f"Markdown conversion error: {str(e)}")

    def convert_pptx_to_pdf(self) -> str:
        """Convert PPTX file to PDF format."""
        self.logger.info(f"Converting PPTX to PDF: {self.file_path}")
        original_name = Path(self.file_path).stem
        output_path = self._generate_unique_filename(original_name, ".pdf")

        try:
            prs = Presentation(self.file_path)
            c = canvas.Canvas(output_path, pagesize=letter)
            _, height = letter

            self.logger.debug(f"Processing {len(prs.slides)} slides...")

            for i, slide in enumerate(prs.slides):
                if i > 0:
                    c.showPage()

                y = height - 40
                c.setFont("Helvetica", 12)
                c.drawString(40, y, f"Slide {i + 1}")
                y -= 30

                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        for line in shape.text.split("\n"):
                            if y < 40:
                                c.showPage()
                                y = height - 40
                            c.drawString(40, y, line[:100])
                            y -= 15
            c.save()
            self.logger.info(f"PPTX successfully converted to PDF: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"PPTX conversion failed: {str(e)}")
            raise Exception(f"PPTX conversion error: {str(e)}")

    def convert_to_pdf(self) -> str:
        self.logger.info("Starting file conversion to PDF...")

        if self.is_valid_url(self.file_path):
            self.logger.info("Processing as URL")
            return self.convert_url_to_pdf()

        file_type = self.detect_file_type()

        if file_type == "pdf":
            self.logger.info("File is already PDF, no conversion needed")
            return self.file_path
        elif file_type == "images":
            return self.convert_image_to_pdf()
        elif file_type == "web":
            return self.convert_html_to_pdf()
        elif file_type == "markdown":
            return self.convert_markdown_to_pdf()
        elif file_type == "presentations":
            return self.convert_pptx_to_pdf()
        else:
            self.logger.error(f"Unsupported file type: {file_type}")
            raise ValueError(f"Unsupported file type: {file_type}")

    def cleanup(self):
        """Explicit cleanup of all resources"""
        if self.temp_files:
            self.logger.debug(
                f"Cleaning up {len(self.temp_files)} temporary files...",
            )

        for file_path in self.temp_files[:]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Removed temporary file: {file_path}")
                self.temp_files.remove(file_path)
            except Exception as e:
                self.logger.warning(
                    f"Could not remove temporary file {file_path}: {str(e)}",
                )

        gc.collect()
        self.logger.debug("Cleanup completed")

    def __del__(self):
        self.cleanup()

    def initiate_parser(self) -> str:
        """
        Initiates the parser workflow by converting the file to PDF
        and then using PdfParser to extract content.
        """
        self.logger.info("Initiating parser workflow...")

        try:
            pdf_path = self.convert_to_pdf()
            self.logger.info(f"File converted to PDF: {pdf_path}")

            self.logger.info("Initializing PDF parser...")
            pdf_parser_instance = pdf_parser.PdfParser(
                file_path=pdf_path,
                output_dir="extracted_content",
                describe_images=True,
            )

            self.logger.info("Extracting content from PDF...")
            llm_content = pdf_parser_instance.initiate()

            self.logger.info("Parser workflow completed successfully")
            return llm_content

        except Exception as e:
            self.logger.error(f"Parser workflow failed: {str(e)}")
            raise Exception(f"Failed to parse file {self.file_path}: {str(e)}")
        finally:
            self.cleanup()


