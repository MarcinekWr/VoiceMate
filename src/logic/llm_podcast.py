from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os   
from pathlib import Path

load_dotenv()

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOIN"),
    api_key=os.getenv("AZURE_OPENAI_API_KEYY"),
    api_version=os.getenv("API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    model_name=os.getenv("AZURE_OPENAI_MODEL"),
    temperature=0.7,
    max_tokens=8000
)

PROMPT_PATHS = {
    "scientific": Path("src/prompts/scientific_style.txt"),
    "casual": Path("src/prompts/casual_style.txt"),
}

def load_prompt_template(style: str) -> PromptTemplate:
    prompt_text = PROMPT_PATHS[style].read_text(encoding="utf-8")
    return PromptTemplate.from_template(prompt_text)

def generate_podcast_text(style: str, input_text: str) -> str:
    prompt_template = load_prompt_template(style)
    user_prompt = prompt_template.format(input_text=input_text)

    system_prompt = (
        "Jesteś Agentem Podcastu Naukowego. Tworzysz klarowne, edukacyjne podcasty w stylu wykładowym."
        if style == "scientific"
        else "Jesteś Agentem Podcastu Hobbistycznego. Opowiadasz lekko, ciekawie i nieformalnie jak przy kawie."
    )
    print(user_prompt)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    return response.content


if __name__ == "__main__":
    
    input_text = Path("src/logic/llm_text_test_file.txt").read_text(encoding="utf-8")
    output = generate_podcast_text("scientific", input_text)
    print(output)
    # print(os.getenv("API_VERSION"))
    # print(os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    # print(os.getenv("AZURE_OPENAI_ENDPOINT"))