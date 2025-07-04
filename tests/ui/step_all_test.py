from __future__ import annotations

from unittest import mock

import pytest
import streamlit as st

from src.ui.steps import step_all


@pytest.fixture(autouse=True)
def clear_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()

def test_render_auto_pipeline_sets_defaults(monkeypatch):
    monkeypatch.setattr(step_all, "get_secret_env_first", lambda k: "dummy")


    st.session_state.clear_state_on_enter = True
    with (
        mock.patch('streamlit.markdown'),
        mock.patch(
            'streamlit.columns', return_value=(mock.MagicMock(), mock.MagicMock()),
        ),
        mock.patch('streamlit.selectbox', return_value='🔬 Styl naukowy'),
        mock.patch('streamlit.radio', return_value='🆓 Azure (Darmowy)'),
        mock.patch('streamlit.button', return_value=False),
        mock.patch('streamlit.expander', mock.MagicMock()),
        mock.patch('opencensus.ext.azure.log_exporter.AzureLogHandler'),
    ):
        step_all.render_auto_pipeline()
        assert st.session_state.step == 6
        assert st.session_state.clear_state_on_enter == False


def test_render_auto_pipeline_generates_podcast(monkeypatch):
    monkeypatch.setattr(step_all, "get_secret_env_first", lambda k: "dummy")

    monkeypatch.setattr(step_all, 'check_content_safety', lambda x: True)  # ✅ dodane
    monkeypatch.setattr(step_all, 'process_uploaded_file', lambda x: 'dummy content')
    monkeypatch.setattr(step_all, 'generate_plan_content', lambda x: 'dummy plan')
    monkeypatch.setattr(step_all, 'generate_podcast_content', lambda s, l, p: 'dummy podcast')
    monkeypatch.setattr(step_all, 'dialog_to_json', lambda t, p: {'dialog': []})
    monkeypatch.setattr(step_all, 'save_to_file', lambda d, f: None)
    monkeypatch.setattr(step_all, 'generate_audio_from_json', lambda j, p: 'dummy.wav')
    monkeypatch.setattr(step_all, 'upload_to_blob', lambda c, p, n: None)

    st.session_state.processing = False
    st.session_state.clear_state_on_enter = False

    with (
        mock.patch('streamlit.file_uploader', return_value=mock.Mock()),
        mock.patch('streamlit.text_input', return_value=''),
        mock.patch('streamlit.selectbox', return_value='🔬 Styl naukowy'),
        mock.patch('streamlit.radio', return_value='🆓 Azure (Darmowy)'),
        mock.patch('streamlit.button', side_effect=[False, True]),
        mock.patch('streamlit.spinner', return_value=mock.MagicMock()),
        mock.patch('streamlit.success'),
        mock.patch('streamlit.audio'),
        mock.patch('streamlit.warning'),
        mock.patch('streamlit.error'),
        mock.patch('streamlit.columns', return_value=(mock.MagicMock(), mock.MagicMock())),
        mock.patch('streamlit.markdown'),
        mock.patch('streamlit.download_button'),
        mock.patch('streamlit.balloons'),
        mock.patch('streamlit.expander', mock.MagicMock()),
        mock.patch('opencensus.ext.azure.log_exporter.AzureLogHandler'),
        mock.patch('builtins.open', mock.mock_open(read_data=b'data')),
    ):
        step_all.render_auto_pipeline()
        assert st.session_state.podcast_text == 'dummy podcast'
        assert st.session_state.audio_path == 'dummy.wav'
