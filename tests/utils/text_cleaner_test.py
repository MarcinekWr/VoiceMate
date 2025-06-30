from __future__ import annotations

import pytest

from src.utils.text_cleaner import clean_text
from src.utils.text_cleaner import final_cleanup
from src.utils.text_cleaner import normalize_punctuation
from src.utils.text_cleaner import normalize_whitespace
from src.utils.text_cleaner import remove_emojis_and_special_chars
from src.utils.text_cleaner import remove_pdf_artifacts
from src.utils.text_cleaner import remove_references_and_notes
from src.utils.text_cleaner import remove_repeated_chars


class TestTextCleaner:
    """Test suite for text cleaning utilities."""

    def test_clean_text_empty(self):
        """Test clean_text with empty input."""
        assert clean_text('') == ''
        assert clean_text(None) == ''

    def test_clean_text_full(self):
        """Test clean_text with full text processing."""
        input_text = 'Hello World! 😊 [1] This is a test...\nPage 1'
        expected = 'Hello World! This is a test...'
        assert clean_text(input_text) == expected

    def test_remove_pdf_artifacts(self):
        """Test PDF artifact removal."""
        input_text = 'Page 1\nCONFIDENTIAL\nThis is a test\nPage 2'
        result = remove_pdf_artifacts(input_text)
        assert 'Page 1' not in result
        assert 'CONFIDENTIAL' not in result
        assert 'This is a test' in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        input_text = 'Hello\n\nWorld   with    spaces'
        result = normalize_whitespace(input_text)
        assert '\n\n' not in result
        assert '   ' not in result
        assert 'Hello World with spaces' in result

    def test_remove_emojis_and_special_chars(self):
        """Test emoji and special character removal."""
        input_text = 'Hello 😊 World 🌍 Test'
        result = remove_emojis_and_special_chars(input_text)
        assert '😊' not in result
        assert '🌍' not in result
        assert 'Hello World Test' in result

    def test_remove_references_and_notes(self):
        """Test reference and note removal."""
        input_text = 'This is a test[1] with (2) references *footnote\n'
        result = remove_references_and_notes(input_text)
        assert '[1]' not in result
        assert '(2)' not in result
        assert '*footnote' not in result
        assert 'This is a test with references' in result

    def test_normalize_punctuation(self):
        """Test punctuation normalization."""
        input_text = 'Hello–World—Test…'
        result = normalize_punctuation(input_text)
        assert '–' not in result
        assert '—' not in result
        assert '…' not in result
        assert 'Hello-World-Test...' in result

    def test_remove_repeated_chars(self):
        """Test repeated character removal."""
        input_text = 'Hello...World///Test&&&'
        result = remove_repeated_chars(input_text)
        assert '...' not in result
        assert '///' not in result
        assert '&&&' not in result
        assert 'Hello..World//Test&&' in result

    def test_final_cleanup(self):
        """Test final cleanup operations."""
        input_text = '  Hello   World!   '
        result = final_cleanup(input_text)
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
        assert remove_repeated_chars(input_text) == expected
