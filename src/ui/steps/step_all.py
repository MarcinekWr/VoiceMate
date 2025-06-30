import streamlit as st
import os
import json
from src.workflow.process_file import process_uploaded_file, process_url_input
from src.workflow.generation import (
    generate_plan_content,
    generate_podcast_content,
    generate_audio_from_json,
)
from src.workflow.save import save_to_file, dialog_to_json
from src.utils.blob_uploader import upload_to_blob


def render_auto_pipeline():
    if "step" not in st.session_state:
        st.session_state.step = 6
    if "clear_state_on_enter" not in st.session_state:
        st.session_state.clear_state_on_enter = True

    if st.session_state.get("clear_state_on_enter", False):
        st.session_state.clear_state_on_enter = False
        st.session_state.podcast_text = None
        st.session_state.audio_path = None
        st.session_state.is_premium = False

    if "step" not in st.session_state:
        st.session_state.step = 6

    st.markdown(
        """
        <style>
        .centered-header {
            max-width: 900px;
            margin: 0 auto;
            text-align: center;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='centered-header'>", unsafe_allow_html=True)
    st.header("⚡ Tryb Błyskawiczny: Wygeneruj cały podcast jednym kliknięciem")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.expander(
            "ℹ️ Jak to działa? Kliknij, aby zobaczyć instrukcję", expanded=False
        ):
            st.markdown(
                """
            W trybie **błyskawicznym** możesz w kilku krokach wygenerować kompletny podcast audio z dowolnej treści.  
            Oto jak to działa:

            **1. Wybierz źródło treści**
            - Możesz załadować plik (`PDF`, `Markdown`, `HTML`, `PPTX`, a nawet obraz z tekstem).
            - Alternatywnie, możesz wkleić adres URL.

            **2. Wybierz styl narracji**
            - 🔬 *Styl naukowy* – idealny do bardziej poważnych i informacyjnych treści. Świetnie sprawdza się przy materiałach edukacyjnych, szkoleniowych czy raportach.
            - 😊 *Styl swobodny* – luźny i przyjazny ton, który brzmi naturalnie, jak rozmowa przy kawie albo podczas spaceru. Polecany do blogów, streszczeń artykułów i lekkich materiałów.

            **3. Wybierz głos lektora**
            - 🆓 *Azure (Darmowy)* – dostępny w planie bezpłatnym.  
            Głos jest poprawny i zrozumiały, ale może brzmieć nieco robotycznie.
            - 🎯 *ElevenLabs (Premium)* – głos bardziej zaawansowany, naturalny i bogaty w barwę.  
            Idealny, jeśli zależy Ci na jakości zbliżonej do prawdziwego lektora.

            **4. Kliknij „Start”**
            - Aplikacja automatycznie wygeneruje:
                - Plan podcastu 🧠  
                - Treść narracji ✍️  
                - JSON dialogowy 🔄  
                - Plik audio do odsłuchu lub pobrania 🎧

            > 💡 Jeśli coś pójdzie nie tak – sprawdź, czy Twój plik/URL zawiera tekst możliwy do odczytu.
            """
            )

        st.subheader("📥 Źródło treści")
        uploaded_file = st.file_uploader(
            "Wybierz plik",
            type=[
                "pdf",
                "jpg",
                "jpeg",
                "png",
                "bmp",
                "tiff",
                "gif",
                "html",
                "htm",
                "md",
                "markdown",
                "pptx",
            ],
        )
        url_input = st.text_input("lub podaj URL", placeholder="https://example.com")

    with col2:
        st.subheader("🎨 Styl podcastu")
        style_labels = {"🔬 Styl naukowy": "scientific", "😊 Styl swobodny": "casual"}
        selected_label = st.selectbox(
            "Wybierz styl:", options=list(style_labels.keys())
        )
        podcast_style = style_labels[selected_label]

        st.subheader("🎧 Silnik audio")
        tts_option = st.radio(
            "Wybierz silnik:", options=["🆓 Azure (Darmowy)", "🎯 ElevenLabs (Premium)"]
        )
        is_premium = "Premium" in tts_option

        if st.button("⬅️ Wróć na stronę główną", type="secondary"):
            st.session_state.clear_state_on_enter = True
            st.session_state.step = 0
            st.rerun()

    st.markdown("<div class='centered-header'>", unsafe_allow_html=True)

    can_process = uploaded_file or (
        url_input.strip().startswith(("http://", "https://"))
    )

    if st.button(
        "🚀 Start – Wygeneruj podcast", type="primary", disabled=not can_process
    ):
        st.session_state.processing = True
        try:
            with st.spinner("📥 Przetwarzanie treści..."):
                llm_content = (
                    process_uploaded_file(uploaded_file)
                    if uploaded_file
                    else process_url_input(url_input.strip())
                )
                if not llm_content:
                    st.error("❌ Nie udało się przetworzyć treści.")
                    return

            with st.spinner("📝 Generowanie planu..."):
                plan_text = generate_plan_content(llm_content)
                if not plan_text:
                    st.error("❌ Nie udało się wygenerować planu.")
                    return

            with st.spinner("🎙️ Generowanie treści podcastu..."):
                podcast_text = generate_podcast_content(
                    podcast_style, llm_content, plan_text
                )
                if not podcast_text:
                    st.error("❌ Nie udało się wygenerować tekstu podcastu.")
                    return

            with st.spinner("🧩 Konwersja do JSON..."):
                json_data = dialog_to_json(podcast_text, is_premium)
                json_filename = (
                    "podcast_premium.json" if is_premium else "podcast_free.json"
                )
                save_to_file(
                    json.dumps(json_data, ensure_ascii=False, indent=2), json_filename
                )

            with st.spinner("🔊 Generowanie audio..."):
                audio_path = generate_audio_from_json(json_data, is_premium)
                try:
                    upload_to_blob("audio", audio_path, os.path.basename(audio_path))
                except Exception as upload_err:
                    st.warning(
                        f"⚠️ Nie udało się wysłać audio do Azure Blob: {upload_err}"
                    )

            st.session_state.step = 6
            st.session_state.podcast_text = podcast_text
            st.session_state.audio_path = audio_path
            st.session_state.is_premium = is_premium

            st.success("✅ Podcast został w pełni wygenerowany!")
            st.audio(audio_path, format="audio/mp3" if is_premium else "audio/wav")

        finally:
            st.session_state.processing = False

    if (
        "podcast_text" in st.session_state
        and st.session_state.podcast_text
        and "audio_path" in st.session_state
        and st.session_state.audio_path
    ):
        col_a, col_b = st.columns(2)

        with col_a:
            st.download_button(
                "📥 Pobierz tekst",
                st.session_state.podcast_text,
                file_name="podcast.txt",
                mime="text/plain",
            )

        with col_b:
            with open(st.session_state.audio_path, "rb") as f:
                st.download_button(
                    "📥 Pobierz audio",
                    f.read(),
                    file_name=os.path.basename(st.session_state.audio_path),
                    mime="audio/mpeg" if is_premium else "audio/wav",
                )

        st.balloons()

    st.markdown("</div>", unsafe_allow_html=True)
