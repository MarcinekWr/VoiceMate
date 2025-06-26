import streamlit as st

def render_home_page():
    st.title("🎙️ VoiceMate ")
    st.markdown("**Generator Podcastów AI — przekształć dowolną treść w podcast audio za pomocą AI**")
    st.markdown("---")
    
    st.markdown("""
    Za pomocą tej aplikacji możesz:
    - 📄 Wgrać dokument lub podać link
    - 🧠 Wygenerować plan podcastu z wykorzystaniem LLM
    - ✍️ Wygenerować tekst podcastu w wybranym stylu
    - 🔄 Skonwertować go na format JSON dialogowy
    - 🎧 Wygenerować audio z użyciem TTS (Azure lub ElevenLabs)

    ---
    Wybierz tryb działania:
    """)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Rozpocznij krok po kroku"):
            st.session_state.step = 1
            st.rerun()

    with col2:
        if st.button("⚡ Szybki podcast (auto)"):
            st.session_state.step = 6
            st.rerun()
