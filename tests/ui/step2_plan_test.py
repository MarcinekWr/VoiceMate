from unittest import mock

import streamlit as st

from src.ui.steps import step2_plan


def test_render_step_2_generate_plan(monkeypatch):
    st.session_state.clear()
    st.session_state.llm_content = 'dummy content'
    st.session_state.processing = False

    monkeypatch.setattr(
        step2_plan,
        'generate_plan_content',
        lambda c: 'dummy plan',
    )

    with mock.patch.object(st, 'button', return_value=True):
        with mock.patch.object(st, 'spinner'):
            with mock.patch.object(st, 'success'):
                with mock.patch.object(st, 'rerun') as mock_rerun:
                    step2_plan.render_step_2()
                    assert st.session_state.step == 3
                    assert st.session_state.plan_text == 'dummy plan'
                    mock_rerun.assert_called()
