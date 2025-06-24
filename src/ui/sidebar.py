import streamlit as st
from workflow.session import reset_workflow

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