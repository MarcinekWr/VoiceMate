"""
Unit tests for validate_env_variables function in src.logic.llm_podcast module.

These tests verify that the function properly checks the presence of required Azure OpenAI environment variables:

- `test_validate_env_variables_success`: Ensures the function executes without errors when all environment variables are set correctly.

- `test_validate_env_variables_missing`: Confirms that the function raises a ValueError with the correct message when a required environment variable is missing.
"""

import os

import pytest

from src.logic.llm_podcast import validate_env_variables
from unittest.mock import patch

def test_validate_env_variables_success(monkeypatch):
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT', 'https://test.endpoint')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test_key')
    monkeypatch.setenv('API_VERSION', '2023-06-01-preview')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'test-deployment')
    monkeypatch.setenv('AZURE_OPENAI_MODEL', 'gpt-4')

    validate_env_variables()


@patch("src.logic.llm_podcast.get_secret_env_first")
def test_validate_env_variables_missing(mock_get):
    mock_get.side_effect = [None, None, None, None, None]

    with pytest.raises(ValueError) as exc:
        validate_env_variables()

    assert 'Missing required environment variables' in str(exc.value)
