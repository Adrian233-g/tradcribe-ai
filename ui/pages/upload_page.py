import streamlit as st
import time
from config import Config
from services.batch_service import BatchService

def render_upload_page():
    st.markdown("### 📤 Carga y Traducción de Artículos en Lote")
    st.write("Sube múltiples artículos académicos o técnicos para procesarlos y traducirlos en paralelo o secuencia con agentes inteligentes.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Selecciona o arrastra los archivos del lote (PDF, DOCX, TXT, Markdown):",
            type=["pdf", "docx", "doc", "txt", "md"],
            accept_multiple_files=True,
            help="Puedes cargar de 1 a 50+ artículos a la vez."
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_files:
            st.markdown("#### 📋 Artículos en cola para procesar:")
            total_size_mb = sum([len(f.getvalue()) for f in uploaded_files]) / (1024 * 1024)
            st.info(f"**{len(uploaded_files)} archivos seleccionados** (Tamaño total: {total_size_mb:.2f} MB)")

            file_details = []
            for f in uploaded_files:
                size_kb = len(f.getvalue()) / 1024
                file_details.append(f"- **{f.name}** ({size_kb:.1f} KB)")
            st.markdown("\n".join(file_details))

    with col2:
        st.markdown('<div class="card-dashboard">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Parámetros del Lote")

        batch_name = st.text_input(
            "Nombre del Lote",
            value=f"Lote_{time.strftime('%Y%m%d_%H%M')}",
            help="Identificador para consultar o descargar posteriormente."
        )

        lang_keys = list(Config.SUPPORTED_LANGUAGES.keys())
        lang_names = list(Config.SUPPORTED_LANGUAGES.values())

        # Idioma Origen (default Inglés)
        source_idx = lang_keys.index("en") if "en" in lang_keys else 0
        source_lang_name = st.selectbox(
            "Idioma Origen",
            options=lang_names,
            index=source_idx
        )
        source_lang = lang_keys[lang_names.index(source_lang_name)]

        # Idioma Destino (default Español)
        target_idx = lang_keys.index("es") if "es" in lang_keys else 1
        target_lang_name = st.selectbox(
            "Idioma Destino",
            options=lang_names,
            index=target_idx
        )
        target_lang = lang_keys[lang_names.index(target_lang_name)]

        # Modo de Traducción
        pipeline_mode = st.radio(
            "Estrategia de Traducción",
            options=[
                ("deepl", "⚡ DeepL API (Ultra-rápido, 1-2 segs)"),
                ("multi_agente", "🧠 Gemini Multi-Agente (Traductor + Crítico + Glosario)"),
                ("gemini_directo", "🚀 Gemini Concurrente Rápido (Traductor + Glosario)"),
                ("web_api", "🌐 API Web de Traducción Externa")
            ],
            format_func=lambda x: x[1],
            index=0
        )[0]

        st.markdown('</div>', unsafe_allow_html=True)

    # Botón de Procesamiento
    st.markdown("<br>", unsafe_allow_html=True)
    if uploaded_files:
        if st.button("🚀 Iniciar Traducción en Lote", type="primary", use_container_width=True):
            gemini_key = st.session_state.get("gemini_key", "").strip()
            deepl_key = st.session_state.get("deepl_key", "").strip()

            if pipeline_mode == "deepl" and not deepl_key:
                st.error("⚠️ Debes ingresar tu **DeepL API Key** en la barra lateral o en la pestaña de Configuración.")
                return

            if pipeline_mode in ["multi_agente", "gemini_directo"] and not gemini_key:
                st.error("⚠️ Debes ingresar tu **Gemini API Key** en la barra lateral o en la pestaña de Configuración para continuar.")
                return

            with st.spinner("Creando lote y extrayendo estructura de los artículos..."):
                try:
                    lote_id = BatchService.create_batch(
                        nombre=batch_name,
                        idioma_origen=source_lang,
                        idioma_destino=target_lang,
                        modo_pipeline=pipeline_mode,
                        uploaded_files=uploaded_files
                    )
                    st.session_state["active_batch_id"] = lote_id
                    st.success(f"✅ ¡Lote #{lote_id} creado con éxito con {len(uploaded_files)} artículos!")
                    st.info("Redirigiendo al monitor de ejecución...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear el lote: {e}")
    else:
        st.info("💡 Por favor, sube uno o más archivos para habilitar el botón de inicio.")
