import streamlit as st
from config import Config
from database.connection import DB_STATUS, DB_TYPE

def render_header():
    """Renderiza el encabezado principal con identidad visual de alto impacto y badge de estado."""
    col1, col2 = st.columns([3, 1.2])
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 0.75rem;">
            <div style="
                background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);
                width: 48px;
                height: 48px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.6rem;
                box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
            ">
                🌐
            </div>
            <div>
                <h1 style="
                    margin: 0;
                    font-size: 1.85rem;
                    font-weight: 800;
                    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #818cf8 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    letter-spacing: -0.5px;
                ">
                    Tradcribe AI
                </h1>
                <p style="margin: 0; color: #94a3b8; font-size: 0.88rem; font-weight: 500;">
                    Plataforma Multi-Agente para Traducción y Estructuración Científica en Lote
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        is_postgres = "PostgreSQL" in DB_STATUS
        status_color = "#34d399" if is_postgres else "#fbbf24"
        pulse_class = "pulse-dot" if is_postgres else ""
        st.markdown(f"""
        <div style="text-align: right; padding-top: 0.6rem;">
            <span style="
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 0.8rem;
                font-weight: 600;
                background: rgba(255, 255, 255, 0.04);
                padding: 0.45rem 0.9rem;
                border-radius: 9999px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                color: #e2e8f0;
            ">
                <span class="status-dot {pulse_class}" style="background: {status_color};"></span>
                {DB_STATUS.split('(')[0].strip()}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border: none; height: 1px; background: linear-gradient(90deg, rgba(99, 102, 241, 0.2) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%); margin: 0.75rem 0 1.25rem 0;'>", unsafe_allow_html=True)

def render_sidebar():
    """Barra lateral estructurada con credenciales, estado de modelos y pipeline."""
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1rem;">
            <span style="font-size: 1.3rem;">⚡</span>
            <span style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9;">Motores & Credenciales</span>
        </div>
        """, unsafe_allow_html=True)

        # Configuración de Gemini API Key en sesión
        if "gemini_key" not in st.session_state:
            st.session_state.gemini_key = Config.GEMINI_API_KEY

        gemini_input = st.text_input(
            "Google Gemini API Key",
            value=st.session_state.gemini_key,
            type="password",
            placeholder="AIzaSy...",
            help="Necesaria para el modo Multi-Agente y Gemini Turbo."
        )
        if gemini_input != st.session_state.gemini_key:
            st.session_state.gemini_key = gemini_input

        # Configuración de DeepL API Key en sesión
        if "deepl_key" not in st.session_state:
            st.session_state.deepl_key = Config.DEEPL_API_KEY

        deepl_input = st.text_input(
            "DeepL API Key (Ultra-rápido)",
            value=st.session_state.deepl_key,
            type="password",
            placeholder="xxxx-xxxx...:fx",
            help="Clave para traducción neural ultra-rápida (Free o Pro)."
        )
        if deepl_input != st.session_state.deepl_key:
            st.session_state.deepl_key = deepl_input

        # Modelo Gemini
        if "gemini_model" not in st.session_state:
            st.session_state.gemini_model = "gemini-2.5-flash"

        model_options = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro"
        ]
        
        current_idx = model_options.index(st.session_state.gemini_model) if st.session_state.gemini_model in model_options else 0

        model_choice = st.selectbox(
            "Modelo Gemini Principal",
            options=model_options,
            index=current_idx,
            help="⚡ gemini-2.5-flash: Modelo de máxima velocidad habilitado en tu cuenta."
        )
        st.session_state.gemini_model = model_choice

        st.markdown("---")
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.75rem;">
            <span style="font-size: 1.1rem;">🧠</span>
            <span style="font-size: 0.95rem; font-weight: 700; color: #f1f5f9;">Arquitectura Multi-Agente</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.9rem; font-size: 0.83rem; line-height: 1.6; color: #cbd5e1;">
            <div style="margin-bottom: 4px;">⚡ <strong style="color:#38bdf8;">DeepL NMT:</strong> 1-2s / doc</div>
            <div style="margin-bottom: 4px;">🚀 <strong style="color:#818cf8;">Gemini Flash:</strong> 3-6s / doc</div>
            <div style="margin-bottom: 4px;">📖 <strong style="color:#34d399;">Glosario:</strong> Memoria terminológica</div>
            <div style="margin-bottom: 4px;">🔍 <strong style="color:#c084fc;">Critic:</strong> Control de calidad</div>
            <div>📦 <strong style="color:#94a3b8;">Builder:</strong> Exportador multi-formato</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Tradcribe AI v1.2 • Motor Concurrente")
