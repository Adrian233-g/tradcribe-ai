import streamlit as st
from config import Config
from database.connection import DB_STATUS, DB_TYPE, get_engine
from sqlalchemy import text

def render_settings_page():
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">
            ⚙️ Configuración y Diagnóstico del Sistema
        </h2>
        <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">
            Verifica el estado de conexión con PostgreSQL, cuotas de DeepL API y modelos habilitados de Google Gemini.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        # PostgreSQL Card
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>🐘</span> Base de Datos PostgreSQL
            </div>
        """, unsafe_allow_html=True)
        st.write(f"**Estado:** `{DB_STATUS}`")
        st.write(f"**Host:** `{Config.DB_HOST}:{Config.DB_PORT}`")
        st.write(f"**Base de Datos:** `{Config.DB_NAME}` | **Usuario:** `{Config.DB_USER}`")

        if st.button("🔄 Probar Conexión a PostgreSQL", use_container_width=True):
            try:
                engine = get_engine()
                with engine.connect() as conn:
                    res = conn.execute(text("SELECT version();")).scalar()
                st.success(f"Conexión exitosa:\n\n`{res}`")
            except Exception as e:
                st.error(f"Error conectando a PostgreSQL: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # DeepL Card
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>⚡</span> Motor DeepL API (NMT)
            </div>
        """, unsafe_allow_html=True)
        deepl_key = st.text_input(
            "DeepL API Key",
            value=st.session_state.get("deepl_key", Config.DEEPL_API_KEY),
            type="password",
            help="Clave para API de DeepL (termina en :fx para el plan Free)."
        )
        if st.button("🧪 Diagnosticar Cuota DeepL", use_container_width=True):
            if not deepl_key:
                st.warning("Ingresa una clave de DeepL primero.")
            else:
                from agents.deepl_translator import DeepLTranslatorAgent
                with st.spinner("Consultando cuota en DeepL API..."):
                    usage = DeepLTranslatorAgent.get_usage(deepl_key)
                    if usage.get("valid"):
                        st.session_state["deepl_key"] = deepl_key.strip()
                        st.success(f"✅ ¡Conexión Exitosa! Plan: **{usage.get('plan_type')}**")
                        chars = usage.get('character_count', 0)
                        limit = usage.get('character_limit', 500000)
                        pct = usage.get('percent_used', 0)
                        st.progress(min(1.0, chars / limit if limit else 0.0))
                        st.write(f"📊 **Consumo mensual:** {chars:,} / {limit:,} caracteres ({pct}%)")

                        # Prueba rápida de traducción
                        agent = DeepLTranslatorAgent(api_key=deepl_key)
                        res, _ = agent.translate_chunk("DeepL API integration is working perfectly.", "en", "es")
                        st.info(f"Traducción de prueba: **{res}**")
                    else:
                        st.error(f"❌ {usage.get('error')}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Gemini Card
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>🤖</span> Google Gemini Multi-Agente
            </div>
        """, unsafe_allow_html=True)
        gemini_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("gemini_key", Config.GEMINI_API_KEY),
            type="password",
            help="Clave para acceder a los modelos Gemini 2.0 / 1.5"
        )
        if st.button("🧪 Diagnosticar Modelos Gemini", use_container_width=True):
            if not gemini_key:
                st.warning("Ingresa tu Gemini API Key primero.")
            else:
                with st.spinner("Consultando catálogo de Google AI Studio..."):
                    import requests
                    clean_k = gemini_key.strip().strip('"').strip("'")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_k}"
                    try:
                        r = requests.get(url, timeout=15)
                        if r.status_code == 200:
                            data = r.json()
                            available = [m['name'].replace("models/", "") for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                            st.success(f"✅ ¡API Key Válida! {len(available)} modelos disponibles.")
                            st.caption(", ".join(available[:8]))

                            from agents.gemini_client import GeminiClient
                            preferred = available[0] if available else "gemini-2.0-flash"
                            test_res = GeminiClient.generate_text("Di: 'Conexión Exitosa'", api_key=clean_k, preferred_model=preferred)
                            st.info(f"Respuesta de prueba ({preferred}): **{test_res}**")
                            st.session_state["gemini_key"] = clean_k
                        else:
                            st.error(f"❌ Error de Google ({r.status_code}):\n{r.text}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Ajustes de Pipeline
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>🧠</span> Parámetros de Agentes
            </div>
        """, unsafe_allow_html=True)
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.slider("Tamaño Chunk (caracteres)", min_value=1000, max_value=6000, value=Config.AGENT_MAX_CHUNK_SIZE, step=500)
        with c_a2:
            st.slider("Temperatura LLM", min_value=0.0, max_value=1.0, value=Config.AGENT_TEMPERATURE, step=0.05)
        st.checkbox("Habilitar Agente Crítico / Revisor de Calidad", value=Config.AGENT_CRITIC_ENABLED)
        st.markdown('</div>', unsafe_allow_html=True)
