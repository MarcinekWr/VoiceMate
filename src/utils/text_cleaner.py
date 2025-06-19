import re
import emoji


def clean_text(text: str) -> str:
    """Clean text content."""
    if not text:
        return ""

    text = remove_pdf_artifacts(text)
    text = normalize_whitespace(text)
    text = remove_emojis_and_special_chars(text)
    text = remove_references_and_notes(text)
    text = normalize_punctuation(text)
    text = final_cleanup(text)

    return text.strip()


def remove_pdf_artifacts(text: str) -> str:
    """Remove common PDF artifacts like headers, footers, and page numbers."""
    text = re.sub(r"\f", "", text)
    text = re.sub(r"Page\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[\u2022•\-–—]+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"CONFIDENTIAL|DRAFT|WATERMARK", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[A-Za-z\s]+\s*\|\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace and line breaks."""
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"\s+", " ", text)
    return text


def remove_emojis_and_special_chars(text: str) -> str:
    """Remove emojis and normalize special characters."""
    text = emoji.replace_emoji(text, replace="")
    return text


def remove_references_and_notes(text: str) -> str:
    """Remove references, footnotes, and other citation markers."""
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\(\d+\)", "", text)
    text = re.sub(r"\([A-Za-z]+ et al\., \d{4}\)", "", text)
    text = re.sub(r"\*\s?.*?(\n|$)", "", text)
    return text


def normalize_punctuation(text: str) -> str:
    """Normalize punctuation marks and quotes."""
    replacements = {
        "–": "-",
        "—": "-",
        "…": "...",
        "‹": "<",
        "›": ">",
        "«": "<<",
        "»": ">>",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def final_cleanup(text: str) -> str:
    """Perform final cleanup operations."""
    text = " ".join(text.split())

    text = remove_repeated_chars(text)

    text = re.sub(r"[^\w\s.,!?-]", "", text)
    return text


def remove_repeated_chars(text: str) -> str:
    """Remove repeated special characters like ., /, & etc. (more than 2 consecutive)."""

    special_chars = r"[.\/&*+=#@$%^(){}[\]|\\:;<>?~`]"

    pattern = f"({special_chars}){{3,}}"
    text = re.sub(pattern, r"\1\1", text)

    return text
