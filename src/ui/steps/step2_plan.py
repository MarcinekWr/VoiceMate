from __future__ import annotations

import streamlit as st

from src.workflow.generation import generate_plan_content


def render_step_2():
    """Render Step 2: Plan Generation"""
    st.header('📝 Krok 2: Generuj plan podcastu')

    st.markdown(
        """
    🔧 Na podstawie przetworzonej treści z pliku/strony internetowej, w tym kroku zostanie wygenerowany **szczegółowy plan podcastu**.

    📋 **Co zawiera plan?**
    - Podział na sekcje tematyczne
    - Kluczowe zagadnienia do poruszenia
    - Kolejność omawiania treści

    ✨ Ten plan zostanie użyty w kolejnym kroku do wygenerowania właściwego tekstu podcastu.
    """,
    )

    # Show extracted content preview
    with st.expander('👁️ Podgląd wydobytej treści', expanded=False):
        preview_text = st.session_state.llm_content
        if len(preview_text) > 2000:
            preview_text = (
                preview_text[:2000] +
                '\n\n... (treść została skrócona dla podglądu)'
            )

        st.text_area(
            'Wydobyta treść',
            value=preview_text,
            height=300,
            disabled=True,
            help='To jest treść wydobyta z Twojego pliku, która zostanie użyta do generowania planu podcastu',
        )

    st.markdown('---')

    col1, col2 = st.columns([1, 3])

    with col1:
        generate_plan_button = st.button(
            '📝 Generuj plan',
            type='primary',
            disabled=st.session_state.processing,
            use_container_width=True,
        )

    with col2:
        if st.session_state.processing:
            st.info('🔄 Generowanie planu... To może potrwać kilka minut.')

    if generate_plan_button:
        st.session_state.processing = True

        with st.spinner('🧠 Analizuję treść i tworzę plan podcastu...'):
            plan_text = generate_plan_content(st.session_state.llm_content)

            if plan_text:
                st.session_state.plan_text = plan_text
                st.session_state.step = 3
                st.session_state.processing = False
                st.success('✅ Plan został pomyślnie wygenerowany!')
                st.balloons()
                st.rerun()
            else:
                st.session_state.processing = False
