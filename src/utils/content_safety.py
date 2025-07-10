from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

from src.utils.key_vault import get_secret_env_first

client = ContentSafetyClient(
    endpoint=get_secret_env_first("CONTENT_SAFETY_ENDPOINT"),
    credential=AzureKeyCredential(get_secret_env_first("CONTENT_SAFETY_KEY")),
)


def check_content_safety(text: str) -> bool:
    """
    Check the content of a text string using Azure Content Safety.

    The function splits the input text into chunks of up to 10,000 characters,
    analyzes each chunk for harmful categories (e.g., violence, hate, sexual content),
    and returns whether the content is considered safe.

    Args:
        text (str): The full text to be checked.

    Returns:
        bool: True if the content is safe, False if any segment is flagged as high severity.
    """
    max_len = 10000
    parts = [text[i : i + max_len] for i in range(0, len(text), max_len)]
    for part in parts:
        req = AnalyzeTextOptions(text=part)
        resp = client.analyze_text(options=req)
        for cat in resp.categories_analysis:
            if cat.severity and cat.severity >= 4:
                return False
    return True
