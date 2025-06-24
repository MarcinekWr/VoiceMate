import streamlit as st

from workflow.session import initialize_session_state
from ui.sidebar import render_sidebar
from ui.steps.step1_upload import render_step_1
from ui.steps.step2_plan import render_step_2
from ui.steps.step3_podcast import render_step_3
from ui.steps.step4_json import render_step_4
from ui.steps.step5_audio import render_step_5

def main():
    # Konfiguracja strony
    st.set_page_config(
        page_title="Generator Podcastów AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inicjalizacja sesji
    initialize_session_state()

    # Tytuł i opis główny
    st.title("🎙️ Generator Podcastów AI")
    st.markdown("**Przekształć dowolną treść w profesjonalny podcast audio za pomocą AI**")
    st.markdown("---")

    # Pasek boczny z postępem
    render_sidebar()

    # Routing kroków
    step = st.session_state.step
    if step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3()
    elif step == 4:
        render_step_4()
    elif step == 5:
        render_step_5()

    # Stopka
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "🚀 Powered by AI | 🛠️ Built with Streamlit | 🎵 TTS: Azure & ElevenLabs"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
