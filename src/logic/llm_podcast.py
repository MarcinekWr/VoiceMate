from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os   
from pathlib import Path
import logging
from typing import Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def validate_env_variables() -> None:
    """Validate that all required environment variables are set."""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",  
        "AZURE_OPENAI_API_KEY",   
        "API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_MODEL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")

def create_llm() -> AzureChatOpenAI:
    """Create and configure the Azure OpenAI client."""
    validate_env_variables()
    
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),  
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),          
        api_version=os.getenv("API_VERSION"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        model_name=os.getenv("AZURE_OPENAI_MODEL"),
        temperature=0.7,
        max_tokens=16384
    )

PROMPT_PATHS = {
    "scientific": Path("src/prompts/scientific_style_test.txt"),
    "casual": Path("src/prompts/casual_style.txt"),
    "plan": Path("src/prompts/plan_prompt.txt"),
}

def load_prompt_template(style: str) -> PromptTemplate:
    """Load prompt template from file with error handling."""
    if style not in PROMPT_PATHS:
        raise ValueError(f"Unknown style: {style}. Available styles: {list(PROMPT_PATHS.keys())}")
    
    prompt_path = PROMPT_PATHS[style]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
        return PromptTemplate.from_template(prompt_text)
    except Exception as e:
        logger.error(f"Error loading prompt template from {prompt_path}: {e}")
        raise

def generate_plan(llm: AzureChatOpenAI, input_text: str) -> str:
    """Generate a plan for the podcast based on input text."""
    try:
        prompt_template = load_prompt_template("plan")
        user_prompt = prompt_template.format(input_text=input_text)
        response = llm.invoke([{"role": "user", "content": user_prompt}])
        return response.content
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise

def generate_podcast_text(llm: AzureChatOpenAI, style: str, input_text: str, plan_text: str) -> str:
    """Generate podcast text in specified style."""
    try:
        prompt_template = load_prompt_template(style)
        user_prompt = prompt_template.format(input_text=input_text, plan_text=plan_text)

        system_prompt = (
            "Jesteś Agentem Podcastu Naukowego. Tworzysz klarowne, edukacyjne podcasty w stylu wykładowym."
            if style == "scientific"
            else "Jesteś Agentem Podcastu Hobbistycznego. Opowiadasz lekko, ciekawie i nieformalnie jak przy kawie."
        )

        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return response.content
    except Exception as e:
        logger.error(f"Error generating podcast text: {e}")
        raise

def save_to_file(content: str, filename: str) -> None:
    """Save content to file with error handling."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Content saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving to {filename}: {e}")
        raise

def main():
    """Main function to orchestrate podcast generation."""
    try:
        llm = create_llm()
        
        input_file = Path("src/logic/llm_text_test_file.txt")
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        input_text = input_file.read_text(encoding="utf-8")
        logger.info(f"Loaded input text ({len(input_text)} characters)")
        
        logger.info("Generating plan...")
        plan_text = generate_plan(llm, input_text)
        save_to_file(plan_text, "output_plan.txt")
        
        logger.info("Generating podcast...")
        output = generate_podcast_text(llm, "scientific", input_text, plan_text)
        save_to_file(output, "podcast.txt")
        
        print("Podcast generation completed successfully!")
        print(f"Plan saved to: output_plan.txt")
        print(f"Podcast saved to: podcast.txt")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()