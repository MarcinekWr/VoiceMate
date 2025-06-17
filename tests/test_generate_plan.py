from unittest.mock import MagicMock
from src.logic.llm_podcast import generate_plan
import pytest

def test_generate_plan_success():
    llm_mock = MagicMock()
    llm_mock.invoke.return_value.content = "plan"

    result = generate_plan(llm=llm_mock, input_text="Jak działa turbina wiatrowa?")
    assert "plan" in result
    llm_mock.invoke.assert_called_once()

def test_generate_plan_error_handling():
    llm_mock = MagicMock()
    llm_mock.invoke.side_effect = Exception("LLM failed")

    with pytest.raises(Exception) as exc:
        generate_plan(llm=llm_mock, input_text="test")

    assert "LLM failed" in str(exc.value)
