import pytest
import streamlit as st
from unittest import mock


def test_main_step_0(monkeypatch):
    st.session_state.clear()
    st.session_state.step = 0

    with mock.patch('src.utils.logging_config.setup_logger', return_value=mock.Mock()), \
         mock.patch.object(st, 'set_page_config'):
        import app
        monkeypatch.setattr(app, 'render_home_page', lambda: st.session_state.update({'home_page_rendered': True}))
        app.main()
        assert st.session_state.home_page_rendered

def test_main_step_1(monkeypatch):
    st.session_state.clear()
    st.session_state.step = 1

    with mock.patch('src.utils.logging_config.setup_logger', return_value=mock.Mock()), \
         mock.patch.object(st, 'set_page_config'):
        import app
        monkeypatch.setattr(app, 'render_sidebar', lambda: st.session_state.update({'sidebar_rendered': True}))
        monkeypatch.setattr(app, 'render_step_1', lambda: st.session_state.update({'step_1_rendered': True}))
        app.main()
        assert st.session_state.sidebar_rendered
        assert st.session_state.step_1_rendered
