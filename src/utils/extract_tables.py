"""
PDF Table Parser class to extract tables from PDF files.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import camelot
import pandas as pd

from src.utils.logging_config import get_request_id, get_session_logger


class PDFTableParser:
    """
    A class to extract and manage tables from a PDF file.
    """

    def __init__(self, pdf_path: str):
        """
        Initialize the PDFTableParser.

        Args:
            pdf_path (str): The path to the PDF file.
        """
        self.pdf_path = pdf_path
        self.logger = get_session_logger(get_request_id())

    def extract_tables(
        self,
        pages: str = 'all',
    ) -> list[dict[str, Any]]:
        """
        Extract tables from PDF and return them as structured data.
        """
        try:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages=pages,
                flavor='lattice',
                strip_text='\n',
            )

            extracted_tables = []

            for i, table in enumerate(tables):
                parsing_report = table.parsing_report
                accuracy = parsing_report.get('accuracy', 0)

                df = self._clean_table_dataframe(table.df)

                if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
                    continue

                content_ratio = self._calculate_content_ratio(df)

                if content_ratio > 0.1 or accuracy > 40:
                    table_data = {
                        'table_id': i,
                        'page': table.parsing_report.get('page', 'unknown'),
                        'accuracy': round(accuracy, 2),
                        'content_ratio': round(content_ratio, 2),
                        'shape': df.shape,
                        'data': df.to_dict('records'),
                        'json': df.to_json(
                            orient='records',
                            force_ascii=False,
                        ),
                    }
                    extracted_tables.append(table_data)

            return extracted_tables

        except Exception as e:
            self.logger.error(
                f'Error extracting tables from PDF {self.pdf_path} on pages {pages}: {e}',
            )
            return []

    @staticmethod
    def _clean_table_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a DataFrame by removing empty rows/columns and whitespace.
        """
        cleaned_df = df.copy()

        # Replace empty strings with NA for consistent handling
        cleaned_df.replace('', pd.NA, inplace=True)

        cleaned_df.dropna(how='all', axis=0, inplace=True)
        cleaned_df.dropna(how='all', axis=1, inplace=True)

        cleaned_df = cleaned_df[
            ~cleaned_df.astype(str)
            .apply(
                lambda x: x.str.strip(),
            )
            .eq('')
            .all(axis=1)
        ]

        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

        cleaned_df.reset_index(drop=True, inplace=True)

        return cleaned_df

    @staticmethod
    def _calculate_content_ratio(df: pd.DataFrame) -> float:
        """
        Calculate the ratio of non-empty cells in a DataFrame.
        """
        if df.empty:
            return 0.0

        non_empty_cells = (
            df.astype(str)
            .apply(
                lambda x: x.str.strip() != '',
            )
            .sum()
            .sum()
        )
        total_cells = df.shape[0] * df.shape[1]

        return non_empty_cells / total_cells if total_cells > 0 else 0.0

    @staticmethod
    def format_tables_for_llm(tables: list[dict[str, Any]]) -> str:
        """
        Format extracted tables into a string suitable for LLM processing.
        """
        if not tables:
            return 'No tables found in the document.'

        formatted_output = []
        formatted_output.append('--- EXTRACTED TABLES ---')

        for table in tables:
            formatted_output.append(f"\n=== TABLE {table['table_id']} ===")
            formatted_output.append(f"Page: {table['page']}")
            formatted_output.append(
                f"Size: {table['shape'][0]} rows × {table['shape'][1]} columns",
            )
            formatted_output.append(f"Accuracy: {table['accuracy']}%")
            formatted_output.append(
                f"Content Ratio: {table['content_ratio']}",
            )

            formatted_output.append('\nTable Data (JSON):')
            try:
                json_data = json.loads(table['json'])
                formatted_output.append(
                    json.dumps(
                        json_data,
                        indent=2,
                        ensure_ascii=False,
                    ),
                )
            except Exception:
                formatted_output.append(table['json'])

            formatted_output.append('-' * 50)

        return '\n'.join(formatted_output)
