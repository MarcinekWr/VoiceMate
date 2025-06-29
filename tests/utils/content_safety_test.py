import pytest
from unittest.mock import patch, MagicMock
from src.utils.content_safety import check_content_safety

@patch('src.utils.content_safety.client')
def test_check_content_safety_safe_text(mock_client):
    mock_response = MagicMock()
    mock_response.categories_analysis = []
    mock_client.analyze_text.return_value = mock_response

    result = check_content_safety("Bezpieczny tekst")
    assert result is True

@patch('src.utils.content_safety.client')
def test_check_content_safety_blocked_text(mock_client):
    mock_category = MagicMock()
    mock_category.severity = 4
    mock_response = MagicMock()
    mock_response.categories_analysis = [mock_category]
    mock_client.analyze_text.return_value = mock_response

    result = check_content_safety("Niebezpieczny tekst")
    assert result is False

@patch('src.utils.content_safety.client')
def test_check_content_safety_long_text(mock_client):
    mock_response = MagicMock()
    mock_response.categories_analysis = []
    mock_client.analyze_text.return_value = mock_response

    long_text = "x" * 25000
    result = check_content_safety(long_text)
    assert result is True
    assert mock_client.analyze_text.call_count == 3
