"""
Simple table extraction module for PDF parsing.
Can be imported into PdfParser class to add table extraction capabilities.
"""
from __future__ import annotations

import json
from typing import Any

import camelot
import pandas as pd


def extract_tables_from_pdf(
    pdf_path: str,
    pages: str = 'all',
) -> list[dict[str, Any]]:
    """
    Extract tables from PDF and return them as structured data.
    """
    try:
        tables = camelot.read_pdf(
            pdf_path,
            pages=pages,
            flavor='lattice',
            strip_text='\n',
        )

        extracted_tables = []

        for i, table in enumerate(tables):
            parsing_report = table.parsing_report
            accuracy = parsing_report.get('accuracy', 0)

            df = clean_table_dataframe(table.df)

            if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
                continue

            content_ratio = calculate_content_ratio(df)

            if content_ratio > 0.1 or accuracy > 40:
                table_data = {
                    'table_id': i,
                    'page': table.parsing_report.get('page', 'unknown'),
                    'accuracy': round(accuracy, 2),
                    'content_ratio': round(content_ratio, 2),
                    'shape': df.shape,
                    'data': df.to_dict('records'),
                    'json': df.to_json(orient='records', force_ascii=False),
                }
                extracted_tables.append(table_data)

        return extracted_tables

    except Exception as e:
        print(f'Error extracting tables from {pdf_path}: {e}')
        return []


def clean_table_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a DataFrame by removing empty rows/columns and whitespace.

    Args:
        df (pd.DataFrame): Raw DataFrame from table extraction

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """

    cleaned_df = df.copy()

    cleaned_df = cleaned_df.dropna(how='all', axis=0)
    cleaned_df = cleaned_df.dropna(how='all', axis=1)

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

    cleaned_df = cleaned_df.reset_index(drop=True)

    return cleaned_df


def calculate_content_ratio(df: pd.DataFrame) -> float:
    """
    Calculate the ratio of non-empty cells in a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to analyze

    Returns:
        float: Ratio of non-empty cells (0.0 to 1.0)
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


def format_tables_for_llm(tables: list[dict[str, Any]]) -> str:
    """
    Format extracted tables into a string suitable for LLM processing.

    Args:
        tables (List[Dict]): List of extracted table data

    Returns:
        str: Formatted string representation of tables
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
        formatted_output.append(f"Content Ratio: {table['content_ratio']}")

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
