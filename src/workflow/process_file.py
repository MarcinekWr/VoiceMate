from __future__ import annotations

import os
import tempfile
import traceback
from pathlib import Path

import streamlit as st

from src.file_parser.other_files_parser import FileConverter
from src.utils.logging_config import get_request_id, get_session_logger


def process_url_input(url: str) -> str | None:
    """Process URL and extract LLM content using FileConverter"""
    request_id = get_request_id()
    get_session_logger(request_id)
    try:
        st.info(f'🌐 Przetwarzam URL: {url}')

        converter = FileConverter(
            url, output_dir='assets', request_id=request_id)

        llm_content = converter.initiate_parser()

        return llm_content

    except Exception as e:
        st.error(f'❌ Błąd podczas przetwarzania URL: {str(e)}')
        if st.checkbox('🔍 Pokaż szczegóły błędu'):
            st.error(traceback.format_exc())
        return None


def process_uploaded_file(uploaded_file) -> str | None:
    request_id = get_request_id()
    logger = get_session_logger(request_id)

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(uploaded_file.name).suffix,
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        st.info(f'📁 Przetwarzam plik: {uploaded_file.name}')
        converter = FileConverter(tmp_file_path, output_dir='assets')
        llm_content = converter.initiate_parser()

        os.unlink(tmp_file_path)
        return llm_content

    except Exception as e:
        logger.exception('❌ Błąd podczas przetwarzania pliku')
        st.error(f'❌ Błąd podczas przetwarzania pliku: {str(e)}')
        if st.checkbox('🔍 Pokaż szczegóły błędu'):
            st.error(traceback.format_exc())
        return None
