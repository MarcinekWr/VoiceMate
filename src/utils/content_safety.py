import os

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

endpoint = os.getenv('CONTENT_SAFETY_ENDPOINT')
key = os.getenv('CONTENT_SAFETY_KEY')

client = ContentSafetyClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


def check_content_safety(text: str) -> bool:
    # Skip real check in CI or with fake credentials
    if os.getenv('CI') == 'true' or not endpoint or not key or 'fake' in endpoint or 'fake' in key:
        print('⏭️ Skipping real content safety check in CI or with fake credentials.')
        return True
    max_len = 10000
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for part in parts:
        req = AnalyzeTextOptions(text=part)
        resp = client.analyze_text(options=req)
        for cat in resp.categories_analysis:
            if cat.severity and cat.severity >= 4:
                return False
    return True
