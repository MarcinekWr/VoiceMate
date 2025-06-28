import pytest
import streamlit as st
from unittest import mock
from src.ui.steps import step0_homepage

def test_render_home_page_sets_step(monkeypatch):
    st.session_state.clear()

    with mock.patch.object(st, 'button', side_effect=[True, False]):
        with mock.patch.object(st, 'rerun') as mock_rerun:
            step0_homepage.render_home_page()
            assert st.session_state.step == 1
            mock_rerun.assert_called()
