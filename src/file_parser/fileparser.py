"""FileParser class to parse PDF files and extract text content."""
import re
import logging
import emoji
from pdfminer.high_level import extract_text
from src.common.CONSTANTS import LOG_FILE_PATH


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOG_FILE_PATH,
    filemode="w",
)
logger = logging.getLogger(__name__)


class FileParser:
    """
    A class to parse files and extract relevant information.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.text = ""
        logger.info("Initialized FileParser with file: %s", file_path)

    def parse(self) -> str:
        """
        Parses the file and returns its content.
        """
        try:
            self.text = extract_text(self.file_path)
            logger.info("Successfully parsed the file: %s", self.file_path)
            return self.text
        except Exception as e:
            logger.error("Failed to parse the file: %s", self.file_path)
            raise RuntimeError(f"Error while parsing PDF: {e}") from e

    def get_text(self) -> str:
        """Returns the last extracted text."""
        return self.text


    def clean_data(self) -> str:
        """
        Cleans the extracted text data by removing artifacts, normalizing text,
        and improving readability.
        """
        if not self.text:
            logger.warning("No text to clean. Have you called parse()?")
            return ""

        text = self.text
        text = self._remove_pdf_artifacts(text)
        text = self._normalize_whitespace(text)
        text = self._remove_emojis_and_special_chars(text)
        text = self._remove_references_and_notes(text)
        text = self._normalize_punctuation(text)
        text = self._final_cleanup(text)

        self.text = text.strip()
        logger.info("Text cleaned successfully.")
        return self.text

    def _remove_pdf_artifacts(self, text: str) -> str:
        """Remove common PDF artifacts like headers, footers, and page numbers."""
        # Remove form feed characters
        text = re.sub(r'\f', '', text)
        # Remove page numbers
        text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
        # Remove bullet points at start of lines
        text = re.sub(r'^\s*[\u2022•\-–—]+\s*$', '', text, flags=re.MULTILINE)
        # Remove watermarks
        text = re.sub(r'CONFIDENTIAL|DRAFT|WATERMARK', '', text, flags=re.IGNORECASE)
        # Remove page numbers in format "X of Y"
        text = re.sub(r'\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        # Remove headers/footers that repeat on every page
        text = re.sub(r'^\s*[A-Za-z\s]+\s*\|\s*\d+\s*$', '', text, flags=re.MULTILINE)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks."""
        # Replace single newlines with space
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        # Keep double newlines as paragraph breaks
        text = re.sub(r'\n{2,}', '\n\n', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text

    def _remove_emojis_and_special_chars(self, text: str) -> str:
        """Remove emojis and normalize special characters."""
        # Remove emojis
        text = emoji.replace_emoji(text, replace='')
        return text

    def _remove_references_and_notes(self, text: str) -> str:
        """Remove references, footnotes, and other citation markers."""
        # Remove references like [1], (1), etc.
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\(\d+\)', '', text)
        # Remove footnotes
        text = re.sub(r'\*\s?.*?\n', '', text)
        # Remove citation markers
        text = re.sub(r'\([A-Za-z]+ et al\., \d{4}\)', '', text)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks and quotes."""
        replacements = {
            '–': '-',  
            '—': '-', 
            '…': '...',  
            '‹': '<',  
            '›': '>',  
            '«': '<<',  
            '»': '>>'  
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Perform final cleanup operations."""
        # Remove any remaining multiple spaces
        text = ' '.join(text.split())
        # Remove any remaining special characters
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text


if __name__ == "__main__":
    # Example usage
    path = "assets//oiak.pdf" 
    parser = FileParser(path)
    try:
        content = parser.parse()
        print("Extracted Content:")
        print(content)
        cleaned_content = parser.clean_data()
        print(f"Cleaned Content:{cleaned_content}")
    except RuntimeError as e:
        print(e)
