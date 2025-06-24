import streamlit as st
import os
import tempfile
from pathlib import Path
import traceback
from typing import Optional
import json
import re
from dotenv import load_dotenv

load_dotenv()

from utils.logging_config import setup_logger, set_request_id

setup_logger() 

from file_parser.other_files_parser import FileConverter
from logic.llm_podcast import generate_plan, generate_podcast_text, create_llm
from logic.Azure_TTS import AzureTTSPodcastGenerator
from logic.Elevenlabs_TTS import ElevenlabsTTSPodcastGenerator

def save_to_file(content: str, filename: str, output_dir: str = "output") -> str:
    """Save content to file and return the path"""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path

def dialog_to_json(raw_text: str, is_premium: bool = True) -> list:
    """Convert dialog text to JSON format"""
    speaker_map = {
        "P": "o2xdfKUpc1Bwq7RchZuW", 
        "S": "CLuTGacrAhcIhaJslbXt",  
    } if is_premium else {
        "P": "pl-PL-MarekNeural",
        "S": "pl-PL-ZofiaNeural"
    }

    pattern = re.compile(r"^\[(P|S)\]:\s*(.+?)(?=^\[P\]:|^\[S\]:|\Z)", re.MULTILINE | re.DOTALL)
    matches = pattern.findall(raw_text)
    
    result = []
    for i, (role, text) in enumerate(matches, start=1):
        result.append({
            "order": i,
            "speaker": "professor" if role == "P" else "student",
            "voice_id": speaker_map[role],
            "text": text.strip().replace("\n", " ")
        })
    return result

def initialize_session_state():
    """Initialize all session state variables"""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'llm_content' not in st.session_state:
        st.session_state.llm_content = None
    if 'plan_text' not in st.session_state:
        st.session_state.plan_text = None
    if 'podcast_text' not in st.session_state:
        st.session_state.podcast_text = None
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None
    if 'is_premium' not in st.session_state:
        st.session_state.is_premium = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False
    if 'request_id' not in st.session_state:
        st.session_state.request_id = set_request_id()
    

def reset_workflow():
    """Reset the workflow to start from beginning"""

    st.session_state.step = 1
    st.session_state.llm_content = None
    st.session_state.plan_text = None
    st.session_state.podcast_text = None
    st.session_state.json_data = None
    st.session_state.audio_path = None
    st.session_state.is_premium = False
    st.session_state.processing = False
    st.session_state.file_processed = False
    st.session_state.request_id = set_request_id() 


def process_uploaded_file(uploaded_file) -> Optional[str]:
    """Process uploaded file and extract LLM content using FileConverter"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        st.info(f"📁 Przetwarzam plik: {uploaded_file.name}")
        
        converter = FileConverter(tmp_file_path, output_dir="assets")
        llm_content = converter.initiate_parser()
        
        os.unlink(tmp_file_path)
        
        return llm_content
    
    except Exception as e:
        st.error(f"❌ Błąd podczas przetwarzania pliku: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu"):
            st.error(traceback.format_exc())
        return None

def process_url_input(url: str) -> Optional[str]:
    """Process URL and extract LLM content using FileConverter"""
    try:
        st.info(f"🌐 Przetwarzam URL: {url}")
        
        converter = FileConverter(url, output_dir="assets")
        llm_content = converter.initiate_parser()
        
        return llm_content
    
    except Exception as e:
        st.error(f"❌ Błąd podczas przetwarzania URL: {str(e)}")
        if st.checkbox("🔍 Pokaż szczegóły błędu"):
            st.error(traceback.format_exc())
        return None

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

def render_sidebar():
    """Render sidebar with progress and controls"""
    with st.sidebar:
        st.header("📋 Postęp generowania")
        
        steps = [
            ("📁", "Wczytaj plik"),
            ("📝", "Generuj plan"),
            ("🎙️", "Generuj podcast"),
            ("🔄", "Konwertuj na JSON"),
            ("🎵", "Generuj audio")
        ]
        
        for i, (icon, step_name) in enumerate(steps, 1):
            if i < st.session_state.step:
                st.success(f"✅ {icon} {step_name}")
            elif i == st.session_state.step:
                st.info(f"➡️ {icon} {step_name}")
            else:
                st.write(f"⏸️ {icon} {step_name}")
        
        st.markdown("---")
        
        if st.button("🔄 Rozpocznij od nowa", type="secondary", use_container_width=True):
            reset_workflow()
            st.rerun()
        
        if st.session_state.llm_content:
            st.markdown("---")
            st.subheader("📊 Informacje o treści")
            st.metric("Długość tekstu", f"{len(st.session_state.llm_content):,} znaków")
            st.metric("Liczba słów", f"{len(st.session_state.llm_content.split()):,}")

def render_step_1():
    """Render Step 1: File Upload"""
    st.header("📁 Krok 1: Wczytaj plik")
    st.markdown("Wybierz plik do przetworzenia lub wprowadź URL strony internetowej.")
    
    with st.expander("ℹ️ Obsługiwane formaty", expanded=False):
        st.markdown("""
        **Pliki:**
        - 📄 **PDF** (.pdf)
        - 🖼️ **Obrazy** (.jpg, .jpeg, .png, .bmp, .tiff, .gif)
        - 🌐 **Strony web** (.html, .htm)
        - 📝 **Markdown** (.md, .markdown)
        - 📊 **Prezentacje** (.pptx)
        
        **URL:**
        - Dowolna strona internetowa (http/https)
        """)
    
    uploaded_file = st.file_uploader(
        "🗂️ Wybierz plik",
        type=['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'html', 'htm', 'md', 'markdown', 'pptx'],
        help="Przeciągnij i upuść plik lub kliknij aby wybrać"
    )
    
    st.markdown("**— lub —**")

    url_input = st.text_input(
        "🌐 Wprowadź URL strony internetowej",
        placeholder="https://example.com/article",
        help="Wprowadź pełny URL wraz z protokołem (http/https)"
    )
    
    can_process = uploaded_file is not None or (url_input.strip() and url_input.startswith(('http://', 'https://')))
    
    if url_input.strip() and not url_input.startswith(('http://', 'https://')):
        st.warning("⚠️ URL musi rozpoczynać się od http:// lub https://")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        process_button = st.button(
            "🚀 Przetwórz", 
            type="primary", 
            disabled=not can_process or st.session_state.processing,
            use_container_width=True
        )
    
    with col2:
        if st.session_state.processing:
            st.info("🔄 Przetwarzanie w toku... To może potrwać kilka minut.")
        elif not can_process:
            st.warning("⚠️ Wybierz plik lub wprowadź prawidłowy URL.")
    
    if process_button:
        st.session_state.processing = True
        
        with st.spinner("🔄 Przetwarzanie pliku i wydobywanie treści..."):
            if uploaded_file is not None:
                llm_content = process_uploaded_file(uploaded_file)
            else:
                llm_content = process_url_input(url_input.strip())
            
            if llm_content:
                st.session_state.llm_content = llm_content
                st.session_state.step = 2
                st.session_state.processing = False
                st.session_state.file_processed = True
                st.success("✅ Plik został pomyślnie przetworzony!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False

def render_step_2():
    """Render Step 2: Plan Generation"""
    st.header("📝 Krok 2: Generuj plan podcastu")
    
    # Show extracted content preview
    with st.expander("👁️ Podgląd wydobytej treści", expanded=False):
        preview_text = st.session_state.llm_content
        if len(preview_text) > 2000:
            preview_text = preview_text[:2000] + "\n\n... (treść została skrócona dla podglądu)"
        
        st.text_area(
            "Wydobyta treść",
            value=preview_text,
            height=300,
            disabled=True,
            help="To jest treść wydobyta z Twojego pliku, która zostanie użyta do generowania planu podcastu"
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        generate_plan_button = st.button(
            "📝 Generuj plan", 
            type="primary", 
            disabled=st.session_state.processing,
            use_container_width=True
        )
    
    with col2:
        if st.session_state.processing:
            st.info("🔄 Generowanie planu... To może potrwać kilka minut.")
    
    if generate_plan_button:
        st.session_state.processing = True
        
        with st.spinner("🧠 Analizuję treść i tworzę plan podcastu..."):
            plan_text = generate_plan_content(st.session_state.llm_content)
            
            if plan_text:
                st.session_state.plan_text = plan_text
                st.session_state.step = 3
                st.session_state.processing = False
                st.success("✅ Plan został pomyślnie wygenerowany!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False

def render_step_3():
    """Render Step 3: Podcast Generation"""
    st.header("🎙️ Krok 3: Generuj tekst podcastu")
    
    # Show plan preview
    with st.expander("📋 Podgląd wygenerowanego planu", expanded=True):
        st.text_area(
            "Plan podcastu",
            value=st.session_state.plan_text,
            height=200,
            disabled=True,
            help="Ten plan będzie użyty do wygenerowania tekstu podcastu"
        )
    
    # Podcast style selection
    st.subheader("🎨 Wybierz styl podcastu")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        podcast_style = st.selectbox(
            "Styl podcastu",
            options=["scientific", "casual"],
            index=0,
            help="Wybierz styl, w jakim ma być napisany podcast"
        )
    
    with col2:
        style_descriptions = {
            "scientific": "🔬 Naukowy - precyzyjny, oparty na faktach",
            "casual": "😊 Swobodny - przyjazny, nieformalny ton"
        }
        st.info(style_descriptions[podcast_style])
    
    st.markdown("---")
    
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
    
    if generate_podcast_button:
        st.session_state.processing = True
        
        with st.spinner(f"🎙️ Tworzę tekst podcastu w stylu {podcast_style}..."):
            podcast_text = generate_podcast_content(
                podcast_style,
                st.session_state.llm_content,
                st.session_state.plan_text
            )
            
            if podcast_text:
                st.session_state.podcast_text = podcast_text
                st.session_state.step = 4
                st.session_state.processing = False
                st.success("✅ Tekst podcastu został pomyślnie wygenerowany!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False

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

def render_step_5():
    """Render Step 5: Audio Generation"""
    st.header("🎵 Krok 5: Generuj audio")
    
    # Show JSON preview
    with st.expander("📋 Podgląd JSON", expanded=False):
        st.json(st.session_state.json_data)
    
    # Engine info
    engine_name = "ElevenLabs (Premium)" if st.session_state.is_premium else "Azure TTS (Free)"
    audio_format = "MP3" if st.session_state.is_premium else "WAV"
    
    st.info(f"🎯 **Wybrany silnik:** {engine_name}")
    st.info(f"📁 **Format wyjściowy:** {audio_format}")
    st.info(f"🎙️ **Liczba segmentów:** {len(st.session_state.json_data)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        generate_audio_button = st.button(
            "🎵 Generuj audio", 
            type="primary", 
            disabled=st.session_state.processing,
            use_container_width=True
        )
    
    with col2:
        if st.session_state.processing:
            st.info("🔄 Generowanie audio... To może potrwać kilka minut.")
    
    if generate_audio_button:
        st.session_state.processing = True
        
        with st.spinner(f"🎵 Generuję audio za pomocą {engine_name}..."):
            audio_path = generate_audio_from_json(st.session_state.json_data, st.session_state.is_premium)
            
            if audio_path:
                st.session_state.audio_path = audio_path
                st.session_state.processing = False
                st.success(f"✅ Audio zostało pomyślnie wygenerowane! Zapisano jako: {audio_path}")
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False
    
    # Show audio player if available
    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        st.markdown("---")
        st.subheader("🎧 Wygenerowane audio")
        
        # Audio player
        with open(st.session_state.audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format=f'audio/{audio_format.lower()}')
        
        # Download section
        st.subheader("💾 Pobierz wyniki")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                label="📥 Pobierz plan",
                data=st.session_state.plan_text,
                file_name="plan_podcastu.txt",
                mime="text/plain",
                help="Pobierz plan podcastu jako plik tekstowy"
            )
        
        with col2:
            st.download_button(
                label="📥 Pobierz podcast",
                data=st.session_state.podcast_text,
                file_name="tekst_podcastu.txt",
                mime="text/plain",
                help="Pobierz tekst podcastu jako plik tekstowy"
            )
        
        with col3:
            st.download_button(
                label="📥 Pobierz JSON",
                data=json.dumps(st.session_state.json_data, ensure_ascii=False, indent=2),
                file_name=f"podcast_{'premium' if st.session_state.is_premium else 'free'}.json",
                mime="application/json",
                help="Pobierz dane JSON dla TTS"
            )
        
        with col4:
            with open(st.session_state.audio_path, 'rb') as audio_file:
                st.download_button(
                    label="📥 Pobierz audio",
                    data=audio_file.read(),
                    file_name=f"podcast.{audio_format.lower()}",
                    mime=f"audio/{audio_format.lower()}",
                    help=f"Pobierz wygenerowane audio ({audio_format})"
                )
        
        st.markdown("---")
        st.success("🎉 **Proces zakończony pomyślnie!**")
        st.info("💡 Twój podcast został w pełni wygenerowany i jest gotowy do użycia!")

def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Generator Podcastów AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("🎙️ Generator Podcastów AI")
    st.markdown("**Przekształć dowolną treść w profesjonalny podcast audio za pomocą AI**")
    st.markdown("---")
    
    # Render sidebar
    render_sidebar()
    
    # Render appropriate step
    if st.session_state.step == 1:
        render_step_1()
    elif st.session_state.step == 2:
        render_step_2()
    elif st.session_state.step == 3:
        render_step_3()
    elif st.session_state.step == 4:
        render_step_4()
    elif st.session_state.step == 5:
        render_step_5()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "🚀 Powered by AI | 🛠️ Built with Streamlit | 🎵 TTS: Azure & ElevenLabs"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()