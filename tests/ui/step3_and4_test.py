from __future__ import annotations

from unittest import mock

import pytest
import streamlit as st

from src.ui.steps import step3_and4


def test_render_step_3_and_4_generate_podcast(monkeypatch):
    st.session_state.clear()
    st.session_state.plan_text = 'dummy plan'
    st.session_state.llm_content = 'dummy content'
    st.session_state.processing = False

    monkeypatch.setattr(
        step3_and4,
        'generate_podcast_content',
        lambda s, l, p: 'dummy podcast text',
    )
    monkeypatch.setattr(
        step3_and4,
        'dialog_to_json',
        lambda t, p: {'dialog': []},
    )
    monkeypatch.setattr(step3_and4, 'save_to_file', lambda d, f: 'dummy_path')

    with mock.patch.object(st, 'button', return_value=True):
        with mock.patch.object(st, 'spinner'):
            with mock.patch.object(st, 'success'):
                with mock.patch.object(st, 'rerun') as mock_rerun:
                    step3_and4.render_step_3_and_4()
                    assert st.session_state.step == 5
                    assert (
                        st.session_state.podcast_text == 'dummy podcast text'
                    )
                    mock_rerun.assert_called()
