from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

load_dotenv()

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOIN"),
    api_key=os.getenv("AZURE_OPENAI_API_KEYY"),
    api_version=os.getenv("API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    model_name=os.getenv("AZURE_OPENAI_MODEL"),
    temperature=0.7,
)

PROMPT_PATHS = {
    "scientific": Path("prompts/scientific_style.txt"),
    "casual": Path("src/prompts/casual_style.txt"),
}


def load_prompt_template(style: str) -> PromptTemplate:
    prompt_text = PROMPT_PATHS[style].read_text(encoding="utf-8")
    return PromptTemplate.from_template(prompt_text)


def generate_podcast_text(style: str, input_text: str) -> str:
    prompt_template = load_prompt_template(style)
    prompt = prompt_template.format(input_text=input_text)
    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    output = generate_podcast_text("scientific", "Podcast o słoniu po polsku")
    print(output)
    # print(os.getenv("API_VERSION"))
    # print(os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    # print(os.getenv("AZURE_OPENAI_ENDPOINT"))
