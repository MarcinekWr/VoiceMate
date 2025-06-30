from __future__ import annotations

import logging
import os
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATHS = {
    'scientific': BASE_DIR / 'prompts' / 'scientific_style.txt',
    'casual': BASE_DIR / 'prompts' / 'casual_style.txt',
    'plan': BASE_DIR / 'prompts' / 'plan_prompt.txt',
}


def validate_env_variables() -> None:
    """Validate that all required environment variables are set."""
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'API_VERSION',
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_MODEL',
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f'Missing required environment variables: {missing_vars}',
        )


def create_llm(ui_callback=None) -> AzureChatOpenAI:
    """Create and configure the Azure OpenAI client."""
    try:
        logger.info('Validating environment variables')
        if ui_callback:
            ui_callback('Sprawdzam zmienne środowiskowe...')

        validate_env_variables()

        logger.info('Creating Azure OpenAI client')
        if ui_callback:
            ui_callback('Tworzę połączenie z Azure OpenAI...')

        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('API_VERSION'),
            deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
            model_name=os.getenv('AZURE_OPENAI_MODEL'),
            temperature=0.7,
            max_tokens=16384,
        )

        logger.info('Azure OpenAI client created successfully')
        if ui_callback:
            ui_callback('Połączenie z AI nawiązane pomyślnie!', 'success')

        return llm
    except Exception as e:
        logger.error(f'Error creating LLM: {e}')
        if ui_callback:
            ui_callback(f'Błąd tworzenia połączenia: {e}', 'error')
        raise


def load_prompt_template(style: str, ui_callback=None) -> PromptTemplate:
    """Load prompt template from file with error handling."""
    prompt_path = None
    try:
        logger.info(f'Loading prompt template for style: {style}')
        if ui_callback:
            ui_callback(f"Ładuję szablon stylu '{style}'...")

        if style not in PROMPT_PATHS:
            error_msg = (
                f'Unknown style: {style}. Available styles: {list(PROMPT_PATHS.keys())}'
            )
            logger.error(error_msg)
            if ui_callback:
                ui_callback(error_msg, 'error')
            raise ValueError(error_msg)

        prompt_path = PROMPT_PATHS[style]
        if not prompt_path.exists():
            error_msg = f'Prompt file not found: {prompt_path}'
            logger.error(error_msg)
            if ui_callback:
                ui_callback(
                    f'Nie znaleziono pliku szablonu: {prompt_path}', 'error',
                )
            raise FileNotFoundError(error_msg)

        prompt_text = prompt_path.read_text(encoding='utf-8')
        template = PromptTemplate.from_template(prompt_text)

        logger.info('Prompt template loaded successfully')
        if ui_callback:
            ui_callback('Szablon załadowany pomyślnie!')

        return template
    except Exception as e:
        logger.error(f'Error loading prompt template from {prompt_path}: {e}')
        if ui_callback:
            ui_callback(f'Błąd ładowania szablonu: {e}', 'error')
        raise


def generate_plan(llm: AzureChatOpenAI, input_text: str, ui_callback=None) -> str:
    """Generate a plan for the podcast based on input text."""
    try:
        if not input_text or not input_text.strip():
            raise ValueError('Input text is empty or only whitespace.')

        logger.info('Starting plan generation')
        if ui_callback:
            ui_callback('Rozpoczynam generowanie planu...')

        prompt_template = load_prompt_template('plan')
        logger.info('Prompt template loaded')
        if ui_callback:
            ui_callback('Szablon załadowany, wysyłam do AI...')

        user_prompt = prompt_template.format(input_text=input_text)
        response = llm.invoke([{'role': 'user', 'content': user_prompt}])

        logger.info('Plan generated successfully')
        if ui_callback:
            ui_callback('Plan wygenerowany!', 'success')

        return response.content
    except Exception as e:
        logger.error(f'Error generating plan: {e}')
        if ui_callback:
            ui_callback(f'Błąd: {e}', 'error')
        raise


def generate_podcast_text(
    llm: AzureChatOpenAI, style: str, input_text: str, plan_text: str, ui_callback=None,
) -> str:
    """Generate podcast text in specified style."""
    try:
        if not input_text or not input_text.strip():
            raise ValueError('Input text is empty or only whitespace.')
        if not plan_text or not plan_text.strip():
            raise ValueError('Plan text is empty or only whitespace.')

        logger.info(f'Starting podcast generation in {style} style')
        if ui_callback:
            ui_callback('Rozpoczynam generowanie podcastu...')

        logger.info('Loading prompt template')
        if ui_callback:
            ui_callback(f"Ładuję szablon stylu '{style}'...")

        prompt_template = load_prompt_template(style)
        user_prompt = prompt_template.format(
            input_text=input_text, plan_text=plan_text,
        )

        logger.info('Preparing system prompt')
        if ui_callback:
            ui_callback('Przygotowuję prompt systemowy...')

        system_prompt = (
            'Jesteś Agentem Podcastu Naukowego. Tworzysz klarowne, edukacyjne podcasty w stylu wykładowym.'
            if style == 'scientific'
            else 'Jesteś Agentem Podcastu Hobbistycznego. Opowiadasz lekko, ciekawie i nieformalnie jak przy kawie.'
        )

        logger.info('Sending request to AI model')
        if ui_callback:
            ui_callback('Wysyłam zapytanie do modelu AI...')

        response = llm.invoke(
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )

        logger.info(
            f'Podcast text generated successfully ({len(response.content)} characters)',
        )
        if ui_callback:
            ui_callback(
                f'Podcast wygenerowany pomyślnie! ({len(response.content)} znaków)',
                'success',
            )

        return response.content
    except Exception as e:
        logger.error(f'Error generating podcast text: {e}')
        if ui_callback:
            ui_callback(f'Błąd generowania podcastu: {e}', 'error')
        raise


def save_to_file(content: str, filename: str) -> None:
    """Save content to file with error handling."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f'Content saved to {filename}')
    except Exception as e:
        logger.error(f'Error saving to {filename}: {e}')
        raise


class LLMPodcastService:
    def __init__(self):
        self.llm = create_llm()

    def run(self):
        """Main logic for generating the podcast."""
        input_file = Path('src/logic/llm_text_test_file.txt')
        if not input_file.exists():
            raise FileNotFoundError(f'Input file not found: {input_file}')

        input_text = input_file.read_text(encoding='utf-8')
        logger.info(f'Loaded input text ({len(input_text)} characters)')

        plan_text = generate_plan(self.llm, input_text)
        save_to_file(plan_text, 'output_plan.txt')

        output = generate_podcast_text(
            self.llm, 'scientific', input_text, plan_text,
        )
        save_to_file(output, 'podcast.txt')

        logger.info('Podcast generation completed successfully!')
