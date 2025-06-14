import streamlit as st
from logic.llm_podcast import generate_podcast_text
from logic.tts import text_to_speech

st.title("🎙️ Podcast Generator z LLM")
st.write("Wprowadź treść i wybierz styl narracji, a my wygenerujemy odcinek podcastu.")

style = st.selectbox("Styl narracji:", ["scientific", "casual"])
input_text = st.text_area("Treść wejściowa", height=200)

if st.button("🎧 Generuj podcast"):
    if not input_text.strip():
        st.warning("Wprowadź treść do przetworzenia.")
    else:
        with st.spinner("Generuję treść..."):
            try:
                output = generate_podcast_text(style, input_text)
                audio_path = "output.mp3"
                text_to_speech(output, filename=audio_path)

                st.success("🎧 Gotowe! Posłuchaj nagrania:")
                st.audio(audio_path, format="audio/mp3")
                st.text_area("📝 Wygenerowany tekst:", output, height=250)
            except Exception as e:
                st.error(f"❌ Wystąpił błąd: {e}")
