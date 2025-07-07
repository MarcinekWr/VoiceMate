from __future__ import annotations

import streamlit as st

from src.utils.logging_config import cleanup_session_logger, set_request_id


def initialize_session_state():
    """Initialize all session state variables"""
    if 'request_id' not in st.session_state:
        st.session_state.request_id = set_request_id()
    if 'step' not in st.session_state:
        st.session_state.step = 0
    if 'llm_content' not in st.session_state:
        st.session_state.llm_content = None
    if 'plan_text' not in st.session_state:
        st.session_state.plan_text = None
    if 'podcast_text' not in st.session_state:
        st.session_state.podcast_text = None
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None
    if 'is_premium' not in st.session_state:
        st.session_state.is_premium = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False


def reset_workflow():
    """Reset the workflow to start from beginning"""

    # Cleanup poprzedniego loggera jeśli istnieje
    if 'request_id' in st.session_state:
        old_request_id = st.session_state.request_id
        try:
            cleanup_session_logger(old_request_id)
        except Exception as e:
            print(f'Error cleaning up logger for {old_request_id}: {e}')

    # Reset wszystkich wartości
    st.session_state.step = 1
    st.session_state.llm_content = None
    st.session_state.plan_text = None
    st.session_state.podcast_text = None
    st.session_state.json_data = None
    st.session_state.audio_path = None
    st.session_state.is_premium = False
    st.session_state.processing = False
    st.session_state.file_processed = False
    st.session_state.request_id = set_request_id()  # Nowy request_id

    # Reset flag dla loggera
    if 'logger_initialized' in st.session_state:
        del st.session_state.logger_initialized


def cleanup_current_session():
    """Funkcja do ręcznego wyczyszczenia aktualnej sesji"""
    if 'request_id' in st.session_state:
        request_id = st.session_state.request_id
        try:
            cleanup_session_logger(request_id)
            st.success(f'Wyczyszczono zasoby dla sesji {request_id}')
        except Exception as e:
            st.error(f'Błąd podczas czyszczenia sesji: {e}')
