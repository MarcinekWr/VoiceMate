"""
This module contains the LLMService class for interacting with Language Models.
"""
from __future__ import annotations

import logging
import os

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI


class LLMService:
    """
    A service class to manage interactions with the Language Model.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm = self._initialize_llm()
        self.is_available = self.llm is not None
        if self.is_available:
            self.logger.info('LLMService setup completed successfully.')

    def _initialize_llm(self) -> AzureChatOpenAI | None:
        """
        Initialize the Azure Chat OpenAI model.
        """
        try:
            llm = AzureChatOpenAI(
                azure_deployment=os.getenv(
                    'AZURE_OPENAI_DEPLOYMENT', 'gpt-4-vision',
                ),
                openai_api_version=os.getenv(
                    'API_VERSION', '2024-02-15-preview',
                ),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                model=os.getenv('AZURE_OPENAI_MODEL', 'gpt-4-vision-preview'),
                max_tokens=4096,
            )
            return llm
        except Exception as e:
            self.logger.error(f'Failed to initialize AzureChatOpenAI: {e}')
            return None

    def generate_description(
        self,
        base64_image: str,
        prompt_template: PromptTemplate,
        topic: str,
    ) -> str:
        """
        Invoke the LLM to generate a description for the given image.
        """
        if not self.is_available:
            return 'LLM service not available'

        try:
            prompt_text = prompt_template.format(topic=topic)
            self.logger.info('Generating image description...')

            message = HumanMessage(
                content=[
                    {'type': 'text', 'text': prompt_text},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64,{base64_image}',
                        },
                    },
                ],
            )

            response = self.llm.invoke([message])
            self.logger.info('Successfully generated image description.')
            return response.content
        except Exception as e:
            self.logger.error(f'Error in LLM invocation: {e}')
            return f'Error generating description: {e}'
