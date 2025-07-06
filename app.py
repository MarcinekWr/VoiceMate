from __future__ import annotations

import logging
import os

import streamlit as st
from dotenv import load_dotenv

from src.common.constants import LOGS_DIR
from src.ui.sidebar import render_sidebar
from src.ui.steps.step0_homepage import render_home_page
from src.ui.steps.step1_upload import render_step_1
from src.ui.steps.step2_plan import render_step_2
from src.ui.steps.step3_and4 import render_step_3_and_4
from src.ui.steps.step5_audio import render_step_5
from src.ui.steps.step_all import render_auto_pipeline
from src.utils.blob_uploader import upload_to_blob
from src.utils.logging_config import (cleanup_session_logger, get_request_id,
                                      get_session_logger, set_request_id)
from src.workflow.session import initialize_session_state

load_dotenv()


def cleanup_on_session_end():
    """Funkcja do czyszczenia zasobów na końcu sesji"""
    if 'request_id' in st.session_state:
        request_id = st.session_state.request_id
        try:
            cleanup_session_logger(request_id)
        except Exception as e:
            print(f'Error cleaning up logger for {request_id}: {e}')


def main():
    st.set_page_config(
        page_title='VoiceMate',
        page_icon='🎙️',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    print('✅ A: przed initialize_session_state()')
    initialize_session_state()
    print('✅ B: po initialize_session_state()')

    # Pobierz request_id z session_state
    request_id = st.session_state.request_id

    # Ustaw request_id w kontekście (dla thread-local storage)
    set_request_id(request_id)

    # Pobierz logger dla tej sesji
    logger = get_session_logger(request_id)

    # Jednorazowe logowanie inicjalizacji
    if 'logger_initialized' not in st.session_state:
        logger.info(f'🟢 Logger gotowy, request_id={request_id}')
        st.session_state.logger_initialized = True

    if st.session_state.step >= 1 and st.session_state.step <= 5:
        render_sidebar()

    step = st.session_state.step

    if step == 0:
        render_home_page()
    elif step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3_and_4()
    elif step == 6:
        render_auto_pipeline()
    elif step == 5:
        render_step_5()

    # Upload logów na końcu sesji
    log_file_path = os.path.join(LOGS_DIR, f'{request_id}.log')
    if os.path.exists(log_file_path):
        try:
            upload_to_blob(
                'logs',
                log_file_path,
                blob_name=os.path.basename(log_file_path),
            )
            logger.info(
                '📤 Logi aplikacji zostały zapisane w Azure Blob Storage.')
            # Opcjonalne: wyświetl info użytkownikowi tylko raz
            if 'blob_upload_notified' not in st.session_state:
                st.success(
                    '📤 Logi aplikacji zostały zapisane w Azure Blob Storage.')
                st.session_state.blob_upload_notified = True
        except Exception as e:
            logger.warning(
                f'⚠️ Nie udało się wysłać logów do Azure Blob Storage: {e}')
            st.warning(
                f'⚠️ Nie udało się wysłać logów do Azure Blob Storage: {e}')

    st.markdown('---')
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        '🚀 Powered by AI | 🛠️ Built with Streamlit | 🎵 TTS: Azure & ElevenLabs'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == '__main__':
    main()
