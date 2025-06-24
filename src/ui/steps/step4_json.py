import streamlit as st
import json

from workflow.save import save_to_file, dialog_to_json

def render_step_4():
    """Render Step 4: JSON Conversion"""
    st.header("🔄 Krok 4: Konwertuj na JSON")
    
    # Show podcast text preview
    with st.expander("🎙️ Podgląd tekstu podcastu", expanded=False):
        st.text_area(
            "Tekst podcastu",
            value=st.session_state.podcast_text,
            height=300,
            disabled=True
        )
    
    # TTS Engine selection
    st.subheader("🎵 Wybierz silnik TTS")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tts_option = st.radio(
            "Silnik TTS",
            options=["Free (Azure TTS)", "Premium (ElevenLabs)"],
            index=0,
            help="Wybierz silnik do generowania audio"
        )
        
        st.session_state.is_premium = tts_option == "Premium (ElevenLabs)"
    
    with col2:
        if st.session_state.is_premium:
            st.info("🎯 **Premium (ElevenLabs)**\n- Wysoka jakość audio\n- Format: MP3\n- Głosy: o2xdfKUpc1Bwq7RchZuW (Profesor), CLuTGacrAhcIhaJslbXt (Student)")
        else:
            st.info("🆓 **Free (Azure TTS)**\n- Dobra jakość audio\n- Format: WAV\n- Głosy: pl-PL-MarekNeural (Profesor), pl-PL-ZofiaNeural (Student)")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        convert_json_button = st.button(
            "🔄 Konwertuj na JSON", 
            type="primary", 
            disabled=st.session_state.processing,
            use_container_width=True
        )
    
    with col2:
        if st.session_state.processing:
            st.info("🔄 Konwertowanie na JSON...")
    
    if convert_json_button:
        st.session_state.processing = True
        
        with st.spinner("🔄 Konwertuję tekst podcastu na format JSON..."):
            try:
                json_data = dialog_to_json(st.session_state.podcast_text, st.session_state.is_premium)
                
                if json_data:
                    st.session_state.json_data = json_data
                    
                    # Save JSON to file
                    json_filename = "podcast_premium.json" if st.session_state.is_premium else "podcast_free.json"
                    json_file_path = save_to_file(json.dumps(json_data, ensure_ascii=False, indent=2), json_filename)
                    
                    st.session_state.step = 5
                    st.session_state.processing = False
                    st.success(f"✅ JSON został pomyślnie wygenerowany! Zapisano jako: {json_file_path}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Nie udało się skonwertować tekstu na JSON")
                    st.session_state.processing = False
                    
            except Exception as e:
                st.error(f"❌ Błąd podczas konwersji na JSON: {str(e)}")
                st.session_state.processing = False