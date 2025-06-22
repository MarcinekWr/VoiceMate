from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils.extract_tables import calculate_content_ratio
from src.utils.extract_tables import clean_table_dataframe
from src.utils.extract_tables import extract_tables_from_pdf
from src.utils.extract_tables import format_tables_for_llm


SAMPLE_DF = pd.DataFrame(
    {'A': ['1', '2', ''], 'B': ['', '3', '4'], 'C': ['5', '', '6']},
)

EMPTY_DF = pd.DataFrame()


MOCK_TABLE_DATA = [
    {
        'table_id': 0,
        'page': 1,
        'accuracy': 95.5,
        'content_ratio': 0.8,
        'shape': (3, 3),
        'data': [{'A': '1', 'B': '2', 'C': '3'}],
        'json': json.dumps([{'A': '1', 'B': '2', 'C': '3'}]),
    },
]


@pytest.fixture
def mock_camelot():
    """Fixture to mock camelot-py."""
    with patch('camelot.read_pdf') as mock_read:
        mock_table = MagicMock()
        mock_table.df = SAMPLE_DF
        mock_table.parsing_report = {'accuracy': 95.5, 'page': 1}
        mock_read.return_value = [mock_table]
        yield mock_read


def test_extract_tables_from_pdf(mock_camelot):
    """Test table extraction from PDF."""
    result = extract_tables_from_pdf('dummy.pdf')
    assert len(result) > 0
    assert 'table_id' in result[0]
    assert 'accuracy' in result[0]
    assert 'content_ratio' in result[0]


def test_extract_tables_empty_pdf(mock_camelot):
    """Test table extraction from empty PDF."""
    mock_camelot.return_value = []
    result = extract_tables_from_pdf('empty.pdf')
    assert len(result) == 0


def test_clean_table_dataframe():
    """Test DataFrame cleaning."""
    result = clean_table_dataframe(SAMPLE_DF)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert len(result.columns) == 3
    assert len(result) == 3


def test_clean_table_dataframe_empty():
    """Test cleaning empty DataFrame."""
    result = clean_table_dataframe(EMPTY_DF)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_calculate_content_ratio():
    """Test content ratio calculation."""
    ratio = calculate_content_ratio(SAMPLE_DF)
    assert isinstance(ratio, float)
    assert 0 <= ratio <= 1


def test_calculate_content_ratio_empty():
    """Test content ratio calculation for empty DataFrame."""
    ratio = calculate_content_ratio(EMPTY_DF)
    assert ratio == 0.0


def test_format_tables_for_llm():
    """Test table formatting for LLM."""
    result = format_tables_for_llm(MOCK_TABLE_DATA)
    assert isinstance(result, str)
    assert 'EXTRACTED TABLES' in result
    assert 'TABLE 0' in result
    assert 'Page: 1' in result
    assert 'Accuracy: 95.5%' in result


def test_format_tables_for_llm_empty():
    """Test formatting empty table list."""
    result = format_tables_for_llm([])
    assert result == 'No tables found in the document.'


@pytest.mark.parametrize(
    'df,expected_ratio',
    [
        (pd.DataFrame({'A': ['1', '2', '3']}), 1.0),
        (pd.DataFrame({'A': ['1', '', '3']}), 0.67),
        (pd.DataFrame({'A': ['', '', '']}), 0.0),
    ],
)
def test_calculate_content_ratio_parametrized(df, expected_ratio):
    """Test content ratio calculation with multiple test cases."""
    ratio = calculate_content_ratio(df)
    # Allow small floating point differences
    assert abs(ratio - expected_ratio) < 0.01


if __name__ == '__main__':
    pytest.main([__file__])
