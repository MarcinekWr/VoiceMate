import streamlit as st
import os
import json
from workflow.process_file import process_uploaded_file, process_url_input
from workflow.generation import generate_plan_content, generate_podcast_content, generate_audio_from_json
from workflow.save import save_to_file, dialog_to_json
from utils.blob_uploader import upload_to_blob

def render_auto_pipeline():
    st.header("⚡ Tryb Błyskawiczny: Wygeneruj cały podcast jednym kliknięciem")

    st.markdown("""
    Ten tryb pozwala na pełne wygenerowanie podcastu w jednym kroku:

    1. Wczytaj plik lub URL
    2. Wybierz styl i silnik audio
    3. Kliknij **Start**, aby wygenerować plan, tekst i plik audio podcastu
    """)

    uploaded_file = st.file_uploader("🗂️ Wybierz plik źródłowy", type=['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'html', 'htm', 'md', 'markdown', 'pptx'])
    url_input = st.text_input("🌐 Lub wprowadź adres URL", placeholder="https://example.com")

    style_labels = {
        "🔬 Styl naukowy": "scientific",
        "😊 Styl swobodny": "casual"
    }
    selected_label = st.selectbox("🎨 Styl podcastu", options=list(style_labels.keys()))
    podcast_style = style_labels[selected_label]

    tts_option = st.radio("🎧 Silnik audio", options=["🆓 Azure (Darmowy)", "🎯 ElevenLabs (Premium)"])
    is_premium = "Premium" in tts_option

    can_process = uploaded_file or (url_input.strip().startswith(("http://", "https://")))

    if st.button("🚀 Start – Wygeneruj cały podcast", type="primary", disabled=not can_process):
        st.session_state.processing = True

        try:
            with st.spinner("📥 Przetwarzanie pliku/URL..."):
                llm_content = process_uploaded_file(uploaded_file) if uploaded_file else process_url_input(url_input.strip())
                if not llm_content:
                    st.error("❌ Nie udało się przetworzyć treści.")
                    return

            with st.spinner("📝 Generowanie planu podcastu..."):
                plan_text = generate_plan_content(llm_content)
                if not plan_text:
                    st.error("❌ Nie udało się wygenerować planu.")
                    return

            with st.spinner("🎙️ Generowanie treści podcastu..."):
                podcast_text = generate_podcast_content(podcast_style, llm_content, plan_text)
                if not podcast_text:
                    st.error("❌ Nie udało się wygenerować tekstu podcastu.")
                    return

            with st.spinner("🧩 Konwersja treści do formatu JSON..."):
                json_data = dialog_to_json(podcast_text, is_premium)
                json_filename = "podcast_premium.json" if is_premium else "podcast_free.json"
                save_to_file(json.dumps(json_data, ensure_ascii=False, indent=2), json_filename)

            with st.spinner("🔊 Generowanie pliku audio..."):
                audio_path = generate_audio_from_json(json_data, is_premium)
                blob_name = os.path.basename(audio_path)
                try:
                    upload_to_blob("audio", audio_path, blob_name)
                except Exception as upload_err:
                    st.warning(f"⚠️ Nie udało się wysłać audio do Azure Blob: {upload_err}")

            st.success("✅ Podcast został w pełni wygenerowany!")
            st.audio(audio_path, format="audio/mp3" if is_premium else "audio/wav")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Pobierz tekst", podcast_text, file_name="podcast.txt")
            with col2:
                with open(audio_path, "rb") as f:
                    st.download_button("📥 Pobierz audio", f.read(), file_name=os.path.basename(audio_path), mime="audio/mpeg" if is_premium else "audio/wav")

            st.balloons()
        finally:
            st.session_state.processing = False
