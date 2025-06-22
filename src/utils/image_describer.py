"""Image description class using Azure OpenAI for describing images."""

from __future__ import annotations

import base64
import io
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from PIL import Image

load_dotenv()

logger = logging.getLogger(__name__)


class ImageDescriber:
    """
    A class to describe images using Azure OpenAI's vision capabilities.
    """

    def __init__(self, prompt_path: str = "src/prompts/image_describer.txt"):
        """
        Initialize the ImageDescriber with Azure OpenAI configuration.

        Args:
            prompt_path: Path to the custom prompt template file
        """
        self.llm: Optional[AzureChatOpenAI] = None
        self.prompt_template: Optional[PromptTemplate] = None
        self.is_available = False
        self.prompt_path = prompt_path

        self._setup_image_describer()

    def _setup_image_describer(self) -> None:
        """Set up the image description LLM and prompt template."""
        try:
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("API_VERSION"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                model_name=os.getenv("AZURE_OPENAI_MODEL"),
            )

            self._load_prompt_template()

            self.is_available = True
            logger.info("ImageDescriber setup completed successfully")

        except ImportError as e:
            logger.warning(
                "Import error setting up image describer: %s. "
                "Check if langchain_openai is installed.",
                e,
            )
            self.is_available = False
        except Exception as e:
            logger.warning(
                "Unexpected error setting up image describer: %s. "
                "Images will be extracted without descriptions.",
                e,
            )
            self.is_available = False

    def _load_prompt_template(self) -> None:
        """Load the prompt template from file or use default."""
        try:
            if os.path.exists(self.prompt_path):
                prompt_text = Path(self.prompt_path).read_text(encoding="utf-8")
                self.prompt_template = PromptTemplate.from_template(prompt_text)
                logger.info("Loaded custom prompt template from %s", self.prompt_path)
            else:
                self._use_default_prompt()
                logger.info("Custom prompt file not found, using default prompt")

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(
                "Failed to load custom prompt from %s: %s. Using default prompt.",
                self.prompt_path,
                e,
            )
            self._use_default_prompt()

    def _use_default_prompt(self) -> None:
        """Set up the default prompt template."""
        default_prompt = (
            "Describe this image in detail. Focus on text, "
            "charts, diagrams, and any important visual elements."
        )
        self.prompt_template = PromptTemplate.from_template(default_prompt)

    def describe_image(self, image_path: str) -> str:
        """
        Describe an image using the configured LLM.
        """
        if not self.is_available or not self.llm or not self.prompt_template:
            return "Image description not available"

        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Convert image to base64
            image_base64 = self._image_to_base64(image_path)

            # Prepare the message for the LLM
            prompt_text = self.prompt_template.format()
            message_content = [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}",
                    },
                },
            ]

            # Get description from LLM
            response = self.llm.invoke([HumanMessage(content=message_content)])
            return response.content

        except FileNotFoundError as e:
            logger.error("Image file not found: %s", e)
            return "Image description not available - file not found"
        except Exception as e:
            logger.error(
                "Unexpected error describing image %s: %s",
                image_path,
                e,
            )
            return f"Error generating description: {str(e)}"

    def _image_to_base64(self, image_path: str) -> str:
        """
        Convert an image file to base64 string.
        """
        with Image.open(image_path) as image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def describe_image_from_bytes(self, image_bytes: bytes) -> str:
        """
        Describe an image from byte data.
        """
        if not self.is_available or not self.llm or not self.prompt_template:
            return "Image description not available"

        try:
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            prompt_text = self.prompt_template.format()
            message_content = [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}",
                    },
                },
            ]

            # Get description from LLM
            response = self.llm.invoke([HumanMessage(content=message_content)])
            return response.content

        except Exception as e:
            logger.error("Unexpected error describing image from bytes: %s", e)
            return f"Error generating description: {str(e)}"
