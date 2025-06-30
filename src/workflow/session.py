import streamlit as st
from src.utils.logging_config import set_request_id


def initialize_session_state():
    """Initialize all session state variables"""
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "llm_content" not in st.session_state:
        st.session_state.llm_content = None
    if "plan_text" not in st.session_state:
        st.session_state.plan_text = None
    if "podcast_text" not in st.session_state:
        st.session_state.podcast_text = None
    if "json_data" not in st.session_state:
        st.session_state.json_data = None
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None
    if "is_premium" not in st.session_state:
        st.session_state.is_premium = False
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "file_processed" not in st.session_state:
        st.session_state.file_processed = False
    if "request_id" not in st.session_state:
        st.session_state.request_id = set_request_id()


def reset_workflow():
    """Reset the workflow to start from beginning"""

    st.session_state.step = 1
    st.session_state.llm_content = None
    st.session_state.plan_text = None
    st.session_state.podcast_text = None
    st.session_state.json_data = None
    st.session_state.audio_path = None
    st.session_state.is_premium = False
    st.session_state.processing = False
    st.session_state.file_processed = False
    st.session_state.request_id = set_request_id()
