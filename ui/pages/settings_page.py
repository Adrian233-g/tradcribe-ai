import streamlit as st
from config import Config
from database.connection import DB_STATUS, DB_TYPE, get_engine
from sqlalchemy import text

def render_settings_page():
    st.markdown("### ⚙️ Configuración y Estado del Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
        st.markdown("#### 🐘 Base de Datos PostgreSQL")
        st.write(f"**Estado actual:** `{DB_STATUS}`")
        st.write(f"**Host:** `{Config.DB_HOST}:{Config.DB_PORT}`")
        st.write(f"**Usuario:** `{Config.DB_USER}`")
        st.write(f"**Base de Datos:** `{Config.DB_NAME}`")

        if st.button("🔄 Probar Conexión a PostgreSQL"):
            try:
                engine = get_engine()
                with engine.connect() as conn:
                    res = conn.execute(text("SELECT version();")).scalar()
                st.success(f"Conexión exitosa a PostgreSQL:\n\n`{res}`")
            except Exception as e:
                st.error(f"Error conectando a PostgreSQL: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Motor DeepL API (Ultra-rápido)")
        deepl_key = st.text_input(
            "DeepL API Key (Free o Pro)",
            value=st.session_state.get("deepl_key", Config.DEEPL_API_KEY),
            type="password",
            help="Clave de API de DeepL (terminada en :fx para el plan gratuito)."
        )
        if st.button("🧪 Diagnosticar y Consultar Cuota DeepL"):
            if not deepl_key:
                st.warning("Ingresa tu clave de DeepL primero.")
            else:
                from agents.deepl_translator import DeepLTranslatorAgent
                with st.spinner("Consultando estado de cuenta en DeepL..."):
                    usage = DeepLTranslatorAgent.get_usage(deepl_key)
                    if usage.get("valid"):
                        st.session_state["deepl_key"] = deepl_key.strip()
                        st.success(f"✅ ¡Conexión con DeepL Exitosa! Plan: **{usage.get('plan_type')}**")
                        chars = usage.get('character_count', 0)
                        limit = usage.get('character_limit', 500000)
                        pct = usage.get('percent_used', 0)
                        st.progress(min(1.0, chars / limit if limit else 0.0))
                        st.write(f"📊 **Consumo mensual:** {chars:,} / {limit:,} caracteres ({pct}%)")

                        # Prueba de traducción
                        agent = DeepLTranslatorAgent(api_key=deepl_key)
                        res, _ = agent.translate_chunk("DeepL API integration is working perfectly.", "en", "es")
                        st.info(f"Traducción de prueba: **{res}**")
                    else:
                        st.error(f"❌ {usage.get('error')}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
        st.markdown("#### 🤖 Modelos de Inteligencia Artificial (Gemini)")
        gemini_key = st.text_input(
            "Google Gemini API Key",
            value=st.session_state.get("gemini_key", Config.GEMINI_API_KEY),
            type="password",
            help="Clave para acceder a los modelos Gemini 1.5/2.0/2.5"
        )
        if st.button("🧪 Diagnosticar y Probar Gemini API"):
            if not gemini_key:
                st.warning("Ingresa una API Key primero.")
            else:
                with st.spinner("Consultando modelos habilitados en Google AI Studio..."):
                    import requests
                    clean_k = gemini_key.strip().strip('"').strip("'")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_k}"
                    try:
                        r = requests.get(url, timeout=15)
                        if r.status_code == 200:
                            data = r.json()
                            available = [m['name'].replace("models/", "") for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                            st.success(f"✅ ¡API Key Válida! Se detectaron {len(available)} modelos habilitados:")
                            st.write(", ".join(available[:8]))

                            # Probar generación
                            from agents.gemini_client import GeminiClient
                            preferred = available[0] if available else "gemini-1.5-flash"
                            test_res = GeminiClient.generate_text("Di: 'Conexión Exitosa'", api_key=clean_k, preferred_model=preferred)
                            st.info(f"Respuesta de prueba ({preferred}): **{test_res}**")
                            st.session_state["gemini_key"] = clean_k
                        else:
                            st.error(f"❌ Error de Google ({r.status_code}):\n{r.text}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
    st.markdown("#### 🧠 Ajustes Finos de los Agentes")
    c_a1, c_a2, c_a3 = st.columns(3)
    with c_a1:
        st.slider("Tamaño Máximo por Fragmento (Caracteres)", min_value=1000, max_value=6000, value=Config.AGENT_MAX_CHUNK_SIZE, step=500)
    with c_a2:
        st.slider("Temperatura del Traductor", min_value=0.0, max_value=1.0, value=Config.AGENT_TEMPERATURE, step=0.05)
    with c_a3:
        st.checkbox("Habilitar Agente Revisor / Crítico", value=Config.AGENT_CRITIC_ENABLED, help="Realiza una segunda pasada de control de calidad, corrección y puntuación.")
    st.markdown('</div>', unsafe_allow_html=True)
