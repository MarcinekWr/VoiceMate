from __future__ import annotations

from unittest import mock

import pytest
import streamlit as st

from src.ui import sidebar


def test_render_sidebar_back_to_home(monkeypatch):
    st.session_state.clear()
    st.session_state.step = 2
    st.session_state.llm_content = 'dummy content'

    with mock.patch.object(st, 'button', side_effect=[True, False, False]):
        with mock.patch.object(st, 'rerun') as mock_rerun:
            sidebar.render_sidebar()
            assert st.session_state.step == 0
            mock_rerun.assert_called()


def test_render_sidebar_reset_workflow(monkeypatch):
    st.session_state.clear()
    st.session_state.step = 3
    st.session_state.llm_content = 'dummy content'

    monkeypatch.setattr(
        sidebar,
        'reset_workflow',
        lambda: st.session_state.update(
            {'llm_content': 'dummy content', 'step': 1},
        ),
    )

    with mock.patch.object(st, 'button', side_effect=[False, True]):
        with mock.patch.object(st, 'rerun') as mock_rerun:
            sidebar.render_sidebar()
            assert st.session_state.llm_content == 'dummy content'
            mock_rerun.assert_called()
