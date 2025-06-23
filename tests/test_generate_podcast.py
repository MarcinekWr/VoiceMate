"""
Unit test for the generate_podcast_text function in src.logic.llm_podcast module.

Test included:

- test_generate_podcast_text_success:
    Ensures that generate_podcast_text correctly returns the expected content
    when the LLM invocation is successful and the input parameters are valid.
"""

from unittest.mock import MagicMock
from src.logic.llm_podcast import generate_podcast_text


def test_generate_podcast_text_success():
    llm_mock = MagicMock()
    llm_mock.invoke.return_value.content = "Podcast odcinek 1"

    result = generate_podcast_text(
        llm=llm_mock,
        style="casual",
        input_text="Jak działa wiatr?",
        plan_text="Plan o wietrze"
    )
    assert "Podcast odcinek 1" in result
    llm_mock.invoke.assert_called_once()
