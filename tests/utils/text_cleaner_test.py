from __future__ import annotations

import pytest

from src.utils.text_cleaner import TextCleaner


def test_clean_text_empty():
    assert TextCleaner('').clean_text() == ''
    assert TextCleaner(None).clean_text() == ''

    def test_clean_text_empty(self):
        """Test clean_text with empty input."""
        assert TextCleaner('').clean_text() == ''
        assert TextCleaner(None).clean_text() == ''

def test_clean_text_no_change():
    assert TextCleaner('This is clean.').clean_text() == 'This is clean.'

    def test_remove_pdf_artifacts(self):
        """Test PDF artifact removal."""
        input_text = 'Page 1\nCONFIDENTIAL\nThis is a test\nPage 2'
        cleaner = TextCleaner(input_text)
        cleaner.remove_pdf_artifacts()
        result = cleaner.text
        assert 'Page 1' not in result
        assert 'CONFIDENTIAL' not in result
        assert 'This is a test' in result

def test_clean_text_comprehensive():
    text = (
        'Page 1\nCONFIDENTIAL\nHello 😊 World 🌍\n'
        'This is a test[1] with (2) notes *footnote\n'
        'Hello...World///Test&&& – end'
    )
    cleaned = TextCleaner(text).clean_text()
    assert 'Page 1' not in cleaned
    assert 'CONFIDENTIAL' not in cleaned
    assert '😊' not in cleaned
    assert '[1]' not in cleaned
    assert '/' not in cleaned or '///' not in cleaned
    assert '–' not in cleaned
    assert '  ' not in cleaned
    assert 'Hello' in cleaned


def test_output_type():
    assert isinstance(TextCleaner('Test.').clean_text(), str)


def test_only_spaces():
    assert TextCleaner('     ').clean_text() == ''


def test_unicode_text():
    text = 'テスト😊123'
    result = TextCleaner(text).clean_text()
    assert '😊' not in result
    assert 'テスト' in result
