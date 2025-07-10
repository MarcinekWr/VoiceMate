from __future__ import annotations

import streamlit as st

from src.utils.content_safety import check_content_safety
from src.workflow.process_file import process_uploaded_file, process_url_input


def render_step_1():
    """Render Step 1: File Upload"""
    st.header("📁 Wczytaj plik")
    st.markdown(
        """
    W tym kroku możesz:

    - 📎 **Przesłać plik** (np. PDF, obraz, prezentację lub dokument HTML/Markdown), **lub**
    - 🌍 **Wprowadzić adres URL** strony internetowej.

    📥 **Co się stanie?**
    Wybrany plik lub treść strony zostanie przetworzona i zinterpretowana przez nasze modele.

    """,
    )

    with st.expander("ℹ️ Obsługiwane formaty", expanded=False):
        st.markdown(
            """
        **Pliki:**
        - 📄 **PDF** (.pdf)
        - 🖼️ **Obrazy** (.jpg, .jpeg, .png, .bmp, .tiff, .gif)
        - 🌐 **Strony web** (.html, .htm)
        - 📝 **Markdown** (.md, .markdown)
        - 📊 **Prezentacje** (.pptx)

        **URL:**
        - Dowolna strona internetowa (http/https)
        """,
        )

    uploaded_file = st.file_uploader(
        "🗂️ Wybierz plik",
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
        help="Przeciągnij i upuść plik lub kliknij aby wybrać",
    )

    st.markdown("**— lub —**")

    url_input = st.text_input(
        "🌐 Wprowadź URL strony internetowej",
        placeholder="https://example.com/article",
        help="Wprowadź pełny URL wraz z protokołem (http/https)",
    )

    can_process = uploaded_file is not None or (
        url_input.strip() and url_input.startswith(("http://", "https://"))
    )

    if url_input.strip() and not url_input.startswith(
        ("http://", "https://"),
    ):
        st.warning("⚠️ URL musi rozpoczynać się od http:// lub https://")

    col1, col2 = st.columns([1, 3])

    with col1:
        process_button = st.button(
            "🚀 Przetwórz",
            type="primary",
            disabled=not can_process or st.session_state.processing,
            use_container_width=True,
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
                if not check_content_safety(llm_content):
                    st.session_state.processing = False
                    st.error("⚠️ Wystąpił błąd.")
                    return
                st.session_state.llm_content = llm_content
                st.session_state.step = 2
                st.session_state.processing = False
                st.session_state.file_processed = True
                st.success("✅ Plik został pomyślnie przetworzony!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False
