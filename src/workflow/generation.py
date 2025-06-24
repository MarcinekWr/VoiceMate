import streamlit as st
import traceback
from typing import Optional

from logic.llm_podcast import generate_plan, generate_podcast_text, create_llm
from logic.Azure_TTS import AzureTTSPodcastGenerator
from logic.Elevenlabs_TTS import ElevenlabsTTSPodcastGenerator
from workflow.save import save_to_file  


def generate_plan_content(llm_content: str) -> Optional[str]:
    """Generate plan from LLM content"""
    try:    
        st.info("🧠 Tworzę LLM...")
        llm = create_llm()
        
        st.info("📝 Generuję plan podcastu...")
        plan_text = generate_plan(llm, llm_content)
        
        plan_file_path = save_to_file(plan_text, "output_plan.txt")
        st.success(f"💾 Plan zapisany do: {plan_file_path}")
        
        return plan_text
    
    except Exception as e:
        st.error(f"❌ Błąd podczas generowania planu: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu planu"):
            st.error(traceback.format_exc())
        return None

def generate_podcast_content(style: str, llm_content: str, plan_text: str) -> Optional[str]:
    """Generate podcast text from plan and content"""
    try:
        st.info("🧠 Tworzę LLM...")
        llm = create_llm()
        
        st.info(f"🎙️ Generuję tekst podcastu w stylu: {style}...")
        podcast_text = generate_podcast_text(llm, style, llm_content, plan_text)
        
        podcast_file_path = save_to_file(podcast_text, "podcast.txt")
        st.success(f"💾 Podcast zapisany do: {podcast_file_path}")
        
        return podcast_text
    
    except Exception as e:
        st.error(f"❌ Błąd podczas generowania podcastu: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu podcastu"):
            st.error(traceback.format_exc())
        return None

def generate_audio_from_json(json_data: list, is_premium: bool) -> Optional[str]:
    """Generate audio from JSON data using appropriate TTS engine"""
    try:
        if is_premium:
            tts = ElevenlabsTTSPodcastGenerator()
            st.info("🎵 Generuję audio z ElevenLabs (Premium - format MP3)...")
            
            def progress_callback(current, total, message):
                progress_bar.progress(current / total)
            
            progress_bar = st.progress(0)
            output_path = tts.generate_podcast_elevenlabs(
                dialog_data=json_data,
                progress_callback=progress_callback
            )
            progress_bar.empty()
            
        else:
            tts = AzureTTSPodcastGenerator()
            st.info("🎵 Generuję audio z Azure TTS (Free - format WAV)...")
            
            def progress_callback(current, total, message):
                progress_bar.progress(current / total)
            
            progress_bar = st.progress(0)
            output_path = tts.generate_podcast_azure(
                dialog_data=json_data,
                progress_callback=progress_callback
            )
            progress_bar.empty()
        
        return output_path
    
    except Exception as e:
        st.error(f"❌ Błąd podczas generowania audio: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu audio"):
            st.error(traceback.format_exc())
        return None