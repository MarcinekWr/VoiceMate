from __future__ import annotations

import pytest

from src.utils.text_cleaner import TextCleaner


class TestTextCleaner:
    """Test suite for text cleaning utilities."""

    def test_clean_text_empty(self):
        """Test clean_text with empty input."""
        assert TextCleaner('').clean_text() == ''
        assert TextCleaner(None).clean_text() == ''

    def test_clean_text_full(self):
        """Test clean_text with full text processing."""
        input_text = 'Sample 😊 text [2] with Page 3 and... extra!!!'
        expected = 'Sample text with and.. extra!!!'
        assert TextCleaner(input_text).clean_text() == expected

    def test_remove_pdf_artifacts(self):
        """Test PDF artifact removal."""
        input_text = 'Page 1\nCONFIDENTIAL\nThis is a test\nPage 2'
        cleaner = TextCleaner(input_text)
        cleaner.remove_pdf_artifacts()
        result = cleaner.text
        assert 'Page 1' not in result
        assert 'CONFIDENTIAL' not in result
        assert 'This is a test' in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        input_text = 'Hello\n\nWorld   with    spaces'
        cleaner = TextCleaner(input_text)
        cleaner.normalize_whitespace()
        result = cleaner.text
        assert '\n\n' not in result
        assert '   ' not in result
        assert 'Hello World with spaces' in result

    def test_remove_emojis_and_special_chars(self):
        """Test emoji and special character removal."""
        input_text = 'Hello 😊 World 🌍 Test'
        cleaner = TextCleaner(input_text)
        cleaner.remove_emojis_and_special_chars()
        result = cleaner.text
        assert '😊' not in result
        assert '🌍' not in result
        assert 'Hello  World  Test' in result

    def test_remove_references_and_notes(self):
        """Test reference and note removal."""
        input_text = 'This is a test[1] with (2) references *footnote\n'
        cleaner = TextCleaner(input_text)
        cleaner.remove_references_and_notes()
        result = cleaner.text
        assert '[1]' not in result
        assert '(2)' not in result
        assert '*footnote' not in result
        assert 'This is a test with  references ' in result

    def test_normalize_punctuation(self):
        """Test punctuation normalization."""
        input_text = 'Hello–World—Test…'
        cleaner = TextCleaner(input_text)
        cleaner.normalize_punctuation()
        result = cleaner.text
        assert '–' not in result
        assert '—' not in result
        assert '…' not in result
        assert 'Hello-World-Test...' in result

    def test_remove_repeated_chars(self):
        """Test repeated character removal."""
        input_text = 'Hello...World///Test&&&'
        cleaner = TextCleaner(input_text)
        cleaner.remove_repeated_chars()
        result = cleaner.text
        assert '...' not in result
        assert '///' not in result
        assert '&&&' not in result
        assert 'Hello..World//Test&&' in result

    def test_final_cleanup(self):
        """Test final cleanup operations."""
        input_text = '  Hello   World!   '
        cleaner = TextCleaner(input_text)
        cleaner.final_cleanup()
        result = cleaner.text
        assert result == 'Hello World!'
        assert '  ' not in result

    @pytest.mark.parametrize(
        'input_text,expected', [
            ('Hello...World', 'Hello..World'),
            ('Test///123', 'Test//123'),
            ('Multiple...dots...here', 'Multiple..dots..here'),
            ('No...repeats', 'No..repeats'),
        ],
    )
    def test_remove_repeated_chars_parametrized(self, input_text, expected):
        """Test remove_repeated_chars with multiple test cases."""
        cleaner = TextCleaner(input_text)
        cleaner.remove_repeated_chars()
        assert cleaner.text == expected
