import streamlit as st
from config import Config
from database.connection import DB_STATUS, DB_TYPE

def render_header():
    """Renderiza el encabezado principal con identidad visual y badge de conexión."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 0.5rem;">
            <div style="font-size: 2.2rem;">🌐</div>
            <div>
                <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Tradcribe AI
                </h1>
                <p style="margin: 0; color: #94a3b8; font-size: 0.95rem; font-weight: 500;">
                    Traducción de Artículos en Lote con Arquitectura Multi-Agente & PostgreSQL
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_color = "#4ade80" if "PostgreSQL" in DB_STATUS else "#facc15"
        st.markdown(f"""
        <div style="text-align: right; padding-top: 0.8rem;">
            <span style="font-size: 0.8rem; background: rgba(255,255,255,0.06); padding: 0.4rem 0.8rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); color: {status_color};">
                ● {DB_STATUS.split('(')[0].strip()}
            </span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<hr style='border: none; height: 1px; background: rgba(255,255,255,0.08); margin: 1rem 0 1.5rem 0;'>", unsafe_allow_html=True)

def render_sidebar():
    """Barra lateral para navegación rápida y estado de API Key."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuración Rápida")

        # Configuración de Gemini API Key en sesión
        if "gemini_key" not in st.session_state:
            st.session_state.gemini_key = Config.GEMINI_API_KEY

        gemini_input = st.text_input(
            "Google Gemini API Key",
            value=st.session_state.gemini_key,
            type="password",
            placeholder="AIzaSy...",
            help="Necesaria para ejecutar el pipeline de traducción multi-agente."
        )
        if gemini_input != st.session_state.gemini_key:
            st.session_state.gemini_key = gemini_input

        # Configuración de DeepL API Key en sesión
        if "deepl_key" not in st.session_state:
            st.session_state.deepl_key = Config.DEEPL_API_KEY

        deepl_input = st.text_input(
            "⚡ DeepL API Key (Ultra-rápido)",
            value=st.session_state.deepl_key,
            type="password",
            placeholder="xxxx-xxxx...:fx",
            help="Clave para traducción instantánea con DeepL API (Free o Pro)."
        )
        if deepl_input != st.session_state.deepl_key:
            st.session_state.deepl_key = deepl_input

        # Modelo Gemini
        if "gemini_model" not in st.session_state:
            st.session_state.gemini_model = Config.GEMINI_MODEL

        model_choice = st.selectbox(
            "Modelo Gemini (Modo Agente)",
            options=["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"],
            index=0
        )
        st.session_state.gemini_model = model_choice

        st.markdown("---")
        st.markdown("### 🤖 Motores & Agentes")
        st.markdown("""
        - ⚡ **DeepL Engine**: Traducción NMT en 1-2s
        - 🧩 **Extractor**: Segmentación semántica
        - 📖 **Glosario**: Memoria terminológica
        - ✍️ **Senior Translator**: Gemini Concurrente
        - 🔍 **Critic / Revisor**: Control de calidad
        - 📦 **Reensamblador**: Exportador DOCX/MD/ZIP
        """)

        st.markdown("---")
        st.caption("Tradcribe AI v1.1 • Motor Dual DeepL & Gemini")
