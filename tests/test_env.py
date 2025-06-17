import os
import pytest
from src.logic.llm_podcast import validate_env_variables

def test_validate_env_variables_success(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.endpoint")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("API_VERSION", "2023-06-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-4")

    validate_env_variables()

def test_validate_env_variables_missing(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError) as exc:
        validate_env_variables()
    assert "AZURE_OPENAI_API_KEY" in str(exc.value)
