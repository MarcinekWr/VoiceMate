import streamlit as st


def render_home_page():
    st.markdown("""
        <style>
        .centered-block {
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }
        button {
            display: block !important;               
            margin-left: auto !important;
            margin-right: auto !important;
            margin-bottom: 10px;
            font-size: 20px;
            padding: 20px 24px !important;
            border-radius: 8px !important;
            width: 50% !important;
        }
        </style>

        <div class='centered-block'>
            <h1 style='text-align: center;'>🎙️ VoiceMate</h1>
            <p style='text-align: center; font-weight: bold; font-size: 20px;'>
                Ucz się słuchając, nie czytając
            </p>
            <hr>
            <p style='text-align: center; font-size: 16px;'>👋 Witaj w aplikacji <strong>VoiceMate</strong> – inteligentnym generatorze podcastów AI!  
            Nasze narzędzie pozwala przekształcić treści dokumentów (PDF, Markdown, HTML i inne), a także strony internetowe (URL), 
            w wciągające podcasty o długości około 5–13 minut.<br><br>Dzięki zaawansowanej analizie dokumentu, VoiceMate tworzy skrócony plan treści i generuje narrację 
            w jednym z dwóch stylów: <strong>🔬 naukowym</strong> lub <strong>😊 hobbystycznym</strong>.  
            Idealne do nauki, słuchania przy kawie lub w podróży!<br><br>🖼️ Nasz system obsługuje także interpretację obrazów w dokumentach – coś, czego większość konkurencji nie oferuje.<br><br><br>
            Do wyboru masz dwa tryby pracy:</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='centered-block'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)

        if st.button("🚀 Rozpocznij krok po kroku", key="step_by_step", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

        st.markdown("""
            <p style='text-align: center; font-size: 14px; max-width: 400px; margin: 0 auto;'>
                Tryb zalecany dla osób, które chcą dokładnie śledzić każdy etap generowania podcastu.  
                Pozwala na ręczne sprawdzenie planu, tekstu i audio krok po kroku – idealne do korekty lub nauki.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)

        if st.button("⚡ Szybki podcast", key="auto_mode", use_container_width=True):
            st.session_state.step = 6
            st.rerun()

        st.markdown("""
            <p style='text-align: center; font-size: 14px; max-width: 400px; margin: 0 auto;'>
                Tryb błyskawiczny generuje kompletny podcast za pomocą jednego kliknięcia.  
                Idealny, gdy zależy Ci na czasie lub chcesz szybko odsłuchać streszczenie dokumentu bez konfiguracji.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


