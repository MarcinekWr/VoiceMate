from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils.extract_tables import PDFTableParser


class TestPDFTableParser(unittest.TestCase):
    """Test suite for the PDFTableParser class."""

    def setUp(self):
        """Set up a mock for the logger."""
        self.patcher = patch("src.utils.extract_tables.logging.getLogger")
        self.mock_get_logger = self.patcher.start()
        self.mock_logger = MagicMock()
        self.mock_get_logger.return_value = self.mock_logger

    def tearDown(self):
        """Stop the patcher."""
        self.patcher.stop()

    @patch("camelot.read_pdf")
    def test_extract_tables_success(self, mock_read_pdf):
        """Test successful extraction of tables."""
        # Arrange
        mock_table = MagicMock()
        mock_table.df = pd.DataFrame(
            {"col1": ["data1", "data2"], "col2": ["data3", "data4"]}
        )
        mock_table.parsing_report = {
            "accuracy": 99.0,
            "whitespace": 1,
            "order": 1,
            "page": 1,
        }
        mock_read_pdf.return_value = [mock_table]

        parser = PDFTableParser("dummy.pdf")

        # Act
        tables = parser.extract_tables()

        # Assert
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["accuracy"], 99.0)
        self.mock_logger.error.assert_not_called()

    @patch("camelot.read_pdf", side_effect=Exception("PDF read error"))
    def test_extract_tables_read_error(self, mock_read_pdf):
        """Test handling of a read error from camelot."""
        # Arrange
        parser = PDFTableParser("dummy.pdf")

        # Act
        tables = parser.extract_tables()

        # Assert
        self.assertEqual(len(tables), 0)
        self.mock_logger.error.assert_called_once()

    def test_clean_table_dataframe(self):
        """Test the dataframe cleaning functionality."""
        # Arrange
        df = pd.DataFrame(
            {
                "A": ["  value1 ", "", " value3 "],
                "B": ["", "", ""],
                "C": [" value2 ", "", ""],
            }
        )
        parser = PDFTableParser("dummy.pdf")

        # Act
        cleaned_df = parser._clean_table_dataframe(df)

        # Assert
        self.assertEqual(cleaned_df.shape, (2, 2))
        self.assertEqual(cleaned_df.iloc[0, 0], "value1")

    def test_calculate_content_ratio(self):
        """Test calculation of content ratio."""
        # Arrange
        df = pd.DataFrame({"A": ["1", "", "3"], "B": ["4", "5", ""]})
        parser = PDFTableParser("dummy.pdf")

        # Act
        ratio = parser._calculate_content_ratio(df)

        # Assert
        self.assertAlmostEqual(ratio, 4 / 6)

    def test_format_tables_for_llm(self):
        """Test formatting of tables for LLM processing."""
        # Arrange
        tables_data = [
            {
                "table_id": 1,
                "page": 1,
                "shape": (2, 2),
                "accuracy": 95.5,
                "content_ratio": 0.8,
                "json": '[{"col1": "a", "col2": "b"}]',
            }
        ]
        parser = PDFTableParser("dummy.pdf")

        # Act
        formatted_string = parser.format_tables_for_llm(tables_data)

        # Assert
        self.assertIn("TABLE 1", formatted_string)
        self.assertIn("Accuracy: 95.5%", formatted_string)


if __name__ == "__main__":
    unittest.main()
