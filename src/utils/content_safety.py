import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

client = ContentSafetyClient(
    endpoint=os.getenv("CONTENT_SAFETY_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("CONTENT_SAFETY_KEY"))
)

def check_content_safety(text: str) -> bool:
    max_len = 10000
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for part in parts:
        req = AnalyzeTextOptions(text=part)
        resp = client.analyze_text(options=req)
        for cat in resp.categories_analysis:
            if cat.severity and cat.severity >= 4:
                return False
    return True
