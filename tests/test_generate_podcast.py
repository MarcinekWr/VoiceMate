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
