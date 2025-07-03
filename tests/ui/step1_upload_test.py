from __future__ import annotations

from unittest import mock

import pytest
import streamlit as st

from src.ui.steps import step1_upload


def test_render_step_1_process_uploaded_file(monkeypatch):
    st.session_state.clear()
    st.session_state.processing = False

    monkeypatch.setattr(
        step1_upload, 'process_uploaded_file', lambda f: 'dummy_content',
    )
    monkeypatch.setattr(step1_upload, 'process_url_input', lambda u: None)

    with mock.patch.object(st, 'file_uploader', return_value=mock.Mock()):
        with mock.patch.object(st, 'text_input', return_value=''):
            with mock.patch.object(st, 'button', return_value=True):
                with mock.patch.object(st, 'spinner'):
                    with mock.patch.object(st, 'success'):
                        with mock.patch.object(st, 'rerun') as mock_rerun:
                            step1_upload.render_step_1()
                            assert st.session_state.step == 2
                            mock_rerun.assert_called()
