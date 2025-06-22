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


def test_clean_text_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_clean_text_no_change():
    assert clean_text("This is clean.") == "This is clean."


def test_clean_text_comprehensive():
    text = (
        "Page 1\nCONFIDENTIAL\nHello 😊 World 🌍\n"
        "This is a test[1] with (2) notes *footnote\n"
        "Hello...World///Test&&& – end"
    )
    cleaned = clean_text(text)
    assert "Page 1" not in cleaned
    assert "CONFIDENTIAL" not in cleaned
    assert "😊" not in cleaned
    assert "[1]" not in cleaned
    assert "///" not in cleaned
    assert "–" not in cleaned
    assert "  " not in cleaned
    assert "Hello" in cleaned


def test_remove_pdf_artifacts():
    text = "Page 1\nCONFIDENTIAL\nThis is a test\nPage 2"
    cleaned = remove_pdf_artifacts(text)
    assert "Page 1" not in cleaned
    assert "CONFIDENTIAL" not in cleaned
    assert "This is a test" in cleaned


def test_normalize_whitespace():
    text = "Hello\n\nWorld   with    spaces"
    result = normalize_whitespace(text)
    assert "\n" not in result
    assert "  " not in result
    assert "Hello World with spaces" in result


def test_remove_emojis_and_special_chars():
    result = remove_emojis_and_special_chars("Hello 😊 World 🌍 Test")
    assert "😊" not in result
    assert "🌍" not in result
    assert result.strip() == "Hello  World  Test"


def test_remove_emojis_and_special_chars_no_change():
    text = "Hello world!"
    assert remove_emojis_and_special_chars(text) == text


def test_remove_references_and_notes():
    text = "This is a test[1] with (2) references *footnote"
    result = remove_references_and_notes(text)
    assert "[1]" not in result
    assert "(2)" not in result
    assert "*footnote" not in result


def test_normalize_punctuation():
    text = "Hello–World—Test…"
    result = normalize_punctuation(text)
    assert "–" not in result
    assert "—" not in result
    assert "…" not in result
    assert result == "Hello-World-Test..."


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello...World", "Hello..World"),
        ("Test///123", "Test//123"),
        ("Multiple...dots...here", "Multiple..dots..here"),
        ("No...repeats", "No..repeats"),
    ],
)
def test_remove_repeated_chars(text, expected):
    assert remove_repeated_chars(text) == expected


def test_final_cleanup():
    input_text = "  Hello   World!   "
    assert final_cleanup(input_text) == "Hello World!"


def test_output_type():
    assert isinstance(clean_text("Test."), str)


def test_only_spaces():
    assert clean_text("     ") == ""


def test_unicode_text():
    text = "テスト😊123"
    result = clean_text(text)
    assert "😊" not in result
    assert "テスト" in result
