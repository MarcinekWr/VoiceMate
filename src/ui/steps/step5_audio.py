import json
import os

import streamlit as st

from src.utils.blob_uploader import upload_to_blob
from src.workflow.generation import generate_audio_from_json


def render_step_5():
    """Render Step 5: Audio Generation"""
    st.header('🎵 Krok 4: Generuj audio')

    # Show JSON preview
    with st.expander('📋 Podgląd JSON', expanded=False):
        st.json(st.session_state.json_data)

    # Engine info
    engine_name = (
        'głosu Elevenlabs (Premium)'
        if st.session_state.is_premium
        else 'głosu azure (Darmowy)'
    )
    audio_format = 'MP3' if st.session_state.is_premium else 'WAV'

    st.info(f'🎯 **Wybrany silnik:** {engine_name}')
    st.info(f'📁 **Format wyjściowy:** {audio_format}')
    st.info(f'🎙️ **Liczba segmentów:** {len(st.session_state.json_data)}')

    st.markdown('---')

    col1, col2 = st.columns([1, 3])

    with col1:
        generate_audio_button = st.button(
            '🎵 Generuj audio',
            type='primary',
            disabled=st.session_state.processing,
            use_container_width=True,
        )

    with col2:
        if st.session_state.processing:
            st.info('🔄 Generowanie audio... To może potrwać kilka minut.')

    if generate_audio_button:
        st.session_state.processing = True

        with st.spinner(f'🎵 Generuję audio za pomocą {engine_name}...'):
            audio_path = generate_audio_from_json(
                st.session_state.json_data,
                st.session_state.is_premium,
            )

            if audio_path:
                st.session_state.audio_path = audio_path

                try:
                    blob_name = os.path.basename(audio_path)
                    upload_to_blob('audio', audio_path, blob_name)
                except Exception as upload_error:
                    st.warning(
                        f'⚠️ Błąd przy wysyłaniu audio do Azure Blob: {upload_error}',
                    )

                st.session_state.processing = False
                st.success(
                    f'✅ Audio zostało pomyślnie wygenerowane! Zapisano jako: {audio_path}',
                )
                st.balloons()
                st.rerun()

    # Show audio player if available
    if st.session_state.audio_path and os.path.exists(
        st.session_state.audio_path,
    ):
        st.markdown('---')
        st.subheader('🎧 Wygenerowane audio')

        # Audio player
        with open(st.session_state.audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format=f'audio/{audio_format.lower()}')

        # Download section
        st.subheader('💾 Pobierz wyniki')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.download_button(
                label='📥 Pobierz plan',
                data=st.session_state.plan_text,
                file_name='plan_podcastu.txt',
                mime='text/plain',
                help='Pobierz plan podcastu jako plik tekstowy',
            )

        with col2:
            st.download_button(
                label='📥 Pobierz podcast',
                data=st.session_state.podcast_text,
                file_name='tekst_podcastu.txt',
                mime='text/plain',
                help='Pobierz tekst podcastu jako plik tekstowy',
            )

        with col3:
            st.download_button(
                label='📥 Pobierz JSON',
                data=json.dumps(
                    st.session_state.json_data,
                    ensure_ascii=False,
                    indent=2,
                ),
                file_name=f"podcast_{'premium' if st.session_state.is_premium else 'free'}.json",
                mime='application/json',
                help='Pobierz dane JSON dla TTS',
            )

        with col4:
            with open(st.session_state.audio_path, 'rb') as audio_file:
                st.download_button(
                    label='📥 Pobierz audio',
                    data=audio_file.read(),
                    file_name=f'podcast.{audio_format.lower()}',
                    mime=f'audio/{audio_format.lower()}',
                    help=f'Pobierz wygenerowane audio ({audio_format})',
                )

        st.markdown('---')
        st.success('🎉 **Proces zakończony pomyślnie!**')
        st.info(
            '💡 Twój podcast został w pełni wygenerowany i jest gotowy do użycia!',
        )
