from __future__ import annotations

from unittest import mock

import pytest
import streamlit as st

from src.ui.steps import step5_audio


def test_render_step_5_generate_audio(monkeypatch):
    st.session_state.clear()
    st.session_state.json_data = {'dummy': 'data'}
    st.session_state.plan_text = 'dummy plan'
    st.session_state.podcast_text = 'dummy podcast'
    st.session_state.is_premium = False
    st.session_state.processing = False
    st.session_state.audio_path = None

    monkeypatch.setattr(
        step5_audio, 'generate_audio_from_json', lambda j, p: 'dummy_audio.wav',
    )
    monkeypatch.setattr(step5_audio, 'upload_to_blob', lambda c, p, n: None)

    with mock.patch.object(st, 'button', return_value=True):
        with mock.patch.object(st, 'spinner'):
            with mock.patch.object(st, 'success'):
                with mock.patch.object(st, 'rerun') as mock_rerun:
                    with mock.patch('os.path.exists', return_value=True):
                        with mock.patch(
                            'builtins.open', mock.mock_open(read_data=b'data'),
                        ):
                            step5_audio.render_step_5()
                            assert st.session_state.audio_path == 'dummy_audio.wav'
                            mock_rerun.assert_called()
