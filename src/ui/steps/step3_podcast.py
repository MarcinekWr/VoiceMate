import streamlit as st

from workflow.generation import generate_podcast_content

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