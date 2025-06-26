import streamlit as st
import json
from src.workflow.generation import generate_podcast_content
from src.workflow.save import save_to_file, dialog_to_json

def render_step_3_and_4():
    """Krok 3: Generowanie tekstu podcastu i wybór silnika TTS"""
    st.header("🎙️ Krok 3: Generuj podcast i wybierz silnik audio")

    # Podgląd planu
    with st.expander("📋 Podgląd wygenerowanego planu", expanded=True):
        st.text_area(
            "Plan podcastu",
            value=st.session_state.plan_text,
            height=200,
            disabled=True,
            help="Ten plan będzie użyty do wygenerowania tekstu podcastu"
        )

    st.subheader("🎨 Ustawienia stylu i głosu")

    with st.container():
        col1, col2 = st.columns([1, 1.5])

        # Styl podcastu
        with col1:
            style_labels = {
                "🔬 Styl naukowy": "scientific",
                "😊 Styl swobodny": "casual"
            }
            label_to_value = list(style_labels.keys())
            selected_label = st.selectbox(
                "Styl tekstu",
                options=label_to_value,
                index=0,
                help="Wybierz styl, w jakim ma być napisany podcast"
            )
            podcast_style = style_labels[selected_label]

        # Silnik TTS
        with col2:
            tts_option = st.radio(
                "Silnik audio",
                options=["🆓 Azure (Darmowy)", "🎯 ElevenLabs (Premium)"],
                index=0,
                help="Wybierz silnik do generowania audio"
            )
            st.session_state.is_premium = "Premium" in tts_option

    # Opis wybranego stylu
    style_descriptions = {
        "scientific": "🔬 *Styl naukowy* – precyzyjny, oparty na faktach",
        "casual": "😊 *Styl swobodny* – przyjazny, nieformalny ton"
    }
    st.caption(style_descriptions[podcast_style])

    # Opis wybranego silnika TTS
    if st.session_state.is_premium:
        st.caption("🎯 *ElevenLabs (Premium)* – najwyższa jakość audio, MP3\nGłosy: Profesor (`o2xdfKUpc1...`), Student (`CLuTGacrAh...`)")
    else:
        st.caption("🆓 *Azure (Darmowy)* – dobra jakość audio, WAV\nGłosy: pl-PL-MarekNeural, pl-PL-ZofiaNeural")

    st.markdown("---")

    # Przycisk generowania
    col1, col2 = st.columns([1, 3])
    with col1:
        generate_podcast_button = st.button(
            "🎙️ Generuj podcast",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True
        )
    with col2:
        if st.session_state.processing:
            st.info("🔄 Generowanie tekstu podcastu... To może potrwać kilka minut.")

    # Logika przycisku
    if generate_podcast_button:
        st.session_state.processing = True
        with st.spinner(f"🎙️ Tworzę tekst podcastu w stylu {podcast_style}..."):
            try:
                podcast_text = generate_podcast_content(
                    podcast_style,
                    st.session_state.llm_content,
                    st.session_state.plan_text
                )
                if podcast_text:
                    st.session_state.podcast_text = podcast_text

                    # Automatyczna konwersja do JSON
                    json_data = dialog_to_json(podcast_text, st.session_state.is_premium)
                    st.session_state.json_data = json_data

                    # Zapis do pliku
                    json_filename = "podcast_premium.json" if st.session_state.is_premium else "podcast_free.json"
                    json_file_path = save_to_file(json.dumps(json_data, ensure_ascii=False, indent=2), json_filename)

                    st.session_state.step = 5
                    st.session_state.processing = False
                    st.success("✅ Podcast został wygenerowany i przygotowany do konwersji audio!")
                    st.balloons()
                    st.rerun()
                else:
                    st.session_state.processing = False
                    st.error("❌ Nie udało się wygenerować podcastu.")
            except Exception as e:
                st.session_state.processing = False
                st.error(f"❌ Wystąpił błąd: {str(e)}")
