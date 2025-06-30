"""Image description class using Azure OpenAI for describing images."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional
from src.common.constants import IMAGE_DESCRIBER_PROMPT_PATH


from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from src.services.llm_service import LLMService
from PIL import Image
import logging


class ImageDescriber:
    """
    A class to describe images using an LLM.
    """

    is_available: bool = False

    def __init__(
        self,
        prompt_path: str = IMAGE_DESCRIBER_PROMPT_PATH,
        llm_service: Optional[LLMService] = None,
    ):
        """
        Initialize the ImageDescriber.
        """
        self.logger = logging.getLogger(__name__)
        self.prompt_path = prompt_path
        self.llm_service = llm_service or LLMService()
        self.prompt_template: Optional[PromptTemplate] = None
        self.is_available = self.llm_service.is_available

        if self.is_available:
            self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> PromptTemplate:
        """Load the prompt template from file or use default."""
        try:
            prompt_path = Path(self.prompt_path)
            if prompt_path.is_file():
                template = prompt_path.read_text(encoding="utf-8")
                self.logger.info(f"Loaded custom prompt from {self.prompt_path}")
                return PromptTemplate.from_template(template)
        except (OSError, UnicodeDecodeError) as e:
            self.logger.error(f"Error reading prompt file {self.prompt_path}: {e}")
        self.logger.info("Using default image description prompt.")
        return self._use_default_prompt()

    def _use_default_prompt(self) -> PromptTemplate:
        """Set up the default prompt template."""
        default_prompt = (
            "Opisz ten obraz szczegółowo. Skup się na tekście, wykresach, diagramach i wszelkich istotnych elementach wizualnych. "
            "Jeśli obraz wygląda na slajd, zrzut ekranu lub dokument, przedstaw uporządkowane podsumowanie jego treści. "
            "Dla dowolnego tematu możesz użyć następującego formatu: "
            "Skup się na {topic}."
        )
        return PromptTemplate.from_template(default_prompt)

    def describe_image(self, image_path: str, topic: str = "general") -> str:
        """
        Describe an image from a file path.
        """
        if not self.is_available:
            return "Image description not available"

        try:
            base64_image = self._image_to_base64(image_path)
            return self.llm_service.generate_description(
                base64_image, self.prompt_template, topic
            )
        except FileNotFoundError:
            self.logger.error(f"File not found: {image_path}")
            return "Image description not available - file not found"
        except Exception as e:
            self.logger.error(f"Error describing image {image_path}: {e}")
            return f"Error generating description: {e}"

    def describe_image_from_bytes(
        self, image_bytes: bytes, topic: str = "general"
    ) -> str:
        """
        Describe an image from bytes.
        """
        if not self.is_available:
            return "Image description not available"

        try:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return self.llm_service.generate_description(
                base64_image, self.prompt_template, topic
            )
        except Exception as e:
            self.logger.error(f"Error describing image from bytes: {e}")
            return f"Error generating description: {e}"

    @staticmethod
    def _image_to_base64(image_path: str) -> str:
        """
        Convert an image file to a base64 encoded string.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
