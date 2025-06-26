import streamlit as st
import os
import tempfile
import traceback
from pathlib import Path
from typing import Optional

from src.file_parser.other_files_parser import FileConverter


def process_url_input(url: str) -> Optional[str]:
    """Process URL and extract LLM content using FileConverter"""
    try:
        st.info(f"🌐 Przetwarzam URL: {url}")
        
        converter = FileConverter(url, output_dir="assets")
        llm_content = converter.initiate_parser()
        
        return llm_content
    
    except Exception as e:
        st.error(f"❌ Błąd podczas przetwarzania URL: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu"):
            st.error(traceback.format_exc())
        return None
    
def process_uploaded_file(uploaded_file) -> Optional[str]:
    """Process uploaded file and extract LLM content using FileConverter"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        st.info(f"📁 Przetwarzam plik: {uploaded_file.name}")
        
        converter = FileConverter(tmp_file_path, output_dir="assets")
        llm_content = converter.initiate_parser()
        
        os.unlink(tmp_file_path)
        
        return llm_content
    
    except Exception as e:
        st.error(f"❌ Błąd podczas przetwarzania pliku: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu"):
            st.error(traceback.format_exc())
        return None