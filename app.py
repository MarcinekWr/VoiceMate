import streamlit as st
import os
import logging

from dotenv import load_dotenv
from src.common.constants import LOGS_DIR
from src.utils.logging_config import setup_logger, get_request_id, set_request_id
from src.workflow.session import initialize_session_state
from src.ui.sidebar import render_sidebar
from src.ui.steps.step1_upload import render_step_1
from src.ui.steps.step2_plan import render_step_2
from src.ui.steps.step_all import render_auto_pipeline
from src.ui.steps.step5_audio import render_step_5
from src.ui.steps.step0_homepage import render_home_page
from src.ui.steps.step3_and4 import render_step_3_and_4
from src.utils.blob_uploader import upload_to_blob

load_dotenv()


if "request_id" not in st.session_state:
    st.session_state.request_id = set_request_id()
else:
    set_request_id(st.session_state.request_id)

log_file_path = os.path.join(LOGS_DIR, f"{get_request_id()}.log")

if "logger_initialized" not in st.session_state:
    logger = setup_logger(log_file_path)
    logger.info(f"🟢 Logger gotowy, request_id={get_request_id()}")
    st.session_state.logger_initialized = True
else:
    logger = logging.getLogger()


def main():
    st.set_page_config(
        page_title="VoiceMate",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state()

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

    if os.path.exists(log_file_path):
        try:
            upload_to_blob(
                "logs", log_file_path, blob_name=os.path.basename(log_file_path)
            )
            st.info("📤 Logi aplikacji zostały zapisane w Azure Blob Storage.")
        except Exception as e:
            st.warning(f"⚠️ Nie udało się wysłać logów do Azure Blob Storage: {e}")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "🚀 Powered by AI | 🛠️ Built with Streamlit | 🎵 TTS: Azure & ElevenLabs"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
