from __future__ import annotations

import re

import emoji


class TextCleaner:
    """Cleans and normalizes text content. self.text will be changed in place by methods."""

    def __init__(self, text: str):
        self.text = text or ''

    def clean_text(self) -> str:
        """Clean text content using all cleaning steps."""
        if not self.text:
            return ''
        self.remove_pdf_artifacts()
        self.normalize_whitespace()
        self.remove_emojis_and_special_chars()
        self.remove_references_and_notes()
        self.normalize_punctuation()
        self.final_cleanup()
        return self.text.strip()

    def remove_pdf_artifacts(self):
        """Remove common PDF artifacts like headers, footers, and page numbers."""
        self.text = re.sub(r'\f', '', self.text)
        self.text = re.sub(r'Page\s*\d+', '', self.text, flags=re.IGNORECASE)
        self.text = re.sub(r'^\s*[\u2022•\-–—]+\s*$',
                           '', self.text, flags=re.MULTILINE)
        self.text = re.sub(
            r'CONFIDENTIAL|DRAFT|WATERMARK',
            '',
            self.text,
            flags=re.IGNORECASE,
        )
        self.text = re.sub(r'\d+\s+of\s+\d+', '',
                           self.text, flags=re.IGNORECASE)
        self.text = re.sub(
            r'^\s*[A-Za-z\s]+\|\s*\d+\s*$',
            '',
            self.text,
            flags=re.MULTILINE,
        )

    def normalize_whitespace(self):
        """Normalize whitespace and line breaks."""
        self.text = re.sub(r'(?<!\n)\n(?!\n)', ' ', self.text)
        self.text = re.sub(r'\n{2,}', '\n\n', self.text)
        self.text = re.sub(r'\s+', ' ', self.text)

    def remove_emojis_and_special_chars(self):
        """Remove emojis and normalize special characters."""
        self.text = emoji.replace_emoji(self.text, replace='')

    def remove_references_and_notes(self):
        """Remove references, footnotes, and other citation markers."""
        self.text = re.sub(r'\[\d+\]', '', self.text)
        self.text = re.sub(r'\(\d+\)', '', self.text)
        self.text = re.sub(r'\([A-Za-z]+ et al\., \d{4}\)', '', self.text)
        self.text = re.sub(r'\*\s?.*?(\n|$)', '', self.text)

    def normalize_punctuation(self):
        """Normalize punctuation marks and quotes."""
        replacements = {
            '–': '-',
            '—': '-',
            '…': '...',
            '‹': '<',
            '›': '>',
            '«': '<<',
            '»': '>>',
        }
        for old, new in replacements.items():
            self.text = self.text.replace(old, new)

    def final_cleanup(self):
        """Perform final cleanup operations."""
        self.text = ' '.join(self.text.split())
        self.remove_repeated_chars()
        self.text = re.sub(r'[^\w\s.,!?-]', '', self.text)

    def remove_repeated_chars(self):
        """Remove repeated special
        characters like ., /, & etc. (more than 2 consecutive)."""
        special_chars = r"[.\/&*+=#@$%^(){}\[\]|\\:;<>?~`\"]"
        pattern = f'({special_chars}){{3,}}'
        self.text = re.sub(pattern, r'\1\1', self.text)
