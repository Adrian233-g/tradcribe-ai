import streamlit as st
import time
from config import Config
from services.batch_service import BatchService

def render_upload_page():
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">
            📤 Carga y Traducción de Artículos en Lote
        </h2>
        <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">
            Sube múltiples artículos académicos, papers o informes técnicos para traducción y estructuración automatizada.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.8, 1.2], gap="large")

    with col1:
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>📁</span> Documentos a Procesar
            </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Selecciona o arrastra los archivos del lote:",
            type=["pdf", "docx", "doc", "txt", "md"],
            accept_multiple_files=True,
            help="Soporta múltiples formatos: PDF nativos/escaneados, Word DOCX, Markdown y Texto plano.",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_files:
            total_bytes = sum([len(f.getvalue()) for f in uploaded_files])
            total_size_mb = total_bytes / (1024 * 1024)

            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin: 1rem 0 0.6rem 0;">
                <span style="font-weight: 700; color: #f1f5f9; font-size: 0.95rem;">
                    Artículos Seleccionados ({len(uploaded_files)})
                </span>
                <span style="font-size: 0.8rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 6px;">
                    {total_size_mb:.2f} MB en total
                </span>
            </div>
            """, unsafe_allow_html=True)

            icons = {"pdf": "📕", "docx": "📄", "doc": "📄", "md": "📝", "txt": "📃"}
            
            for f in uploaded_files:
                ext = f.name.split('.')[-1].lower() if '.' in f.name else "txt"
                icon = icons.get(ext, "📄")
                size_kb = len(f.getvalue()) / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"

                st.markdown(f"""
                <div class="file-chip">
                    <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
                        <span style="font-size: 1.1rem;">{icon}</span>
                        <span style="font-weight: 600; font-size: 0.88rem; color: #f1f5f9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {f.name}
                        </span>
                    </div>
                    <span style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: #94a3b8; margin-left: 12px;">
                        {size_str}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>⚙️</span> Parámetros de Traducción
            </div>
        """, unsafe_allow_html=True)

        batch_name = st.text_input(
            "Nombre del Lote",
            value=f"Lote_{time.strftime('%Y%m%d_%H%M')}",
            help="Etiqueta identificadora para el lote en la base de datos."
        )

        lang_keys = list(Config.SUPPORTED_LANGUAGES.keys())
        lang_names = list(Config.SUPPORTED_LANGUAGES.values())

        c_l1, c_l2 = st.columns(2)
        with c_l1:
            source_idx = lang_keys.index("en") if "en" in lang_keys else 0
            source_lang_name = st.selectbox("Idioma Origen", options=lang_names, index=source_idx)
            source_lang = lang_keys[lang_names.index(source_lang_name)]
        with c_l2:
            target_idx = lang_keys.index("es") if "es" in lang_keys else 1
            target_lang_name = st.selectbox("Idioma Destino", options=lang_names, index=target_idx)
            target_lang = lang_keys[lang_names.index(target_lang_name)]

        st.markdown("<div style='margin-top: 0.8rem; font-weight: 600; font-size: 0.88rem; color: #cbd5e1;'>Estrategia de Motor</div>", unsafe_allow_html=True)
        pipeline_mode = st.radio(
            "Estrategia",
            options=[
                ("gemini_directo", "🚀 Gemini Turbo Concurrente (Ultra-rápido, 3-6s)"),
                ("deepl", "⚡ DeepL NMT (Instantáneo, 1-2s)"),
                ("multi_agente", "🧠 Gemini Multi-Agente (Traductor + Auditor Crítico)"),
                ("web_api", "🌐 API Web Externa")
            ],
            format_func=lambda x: x[1],
            index=0,
            label_visibility="collapsed"
        )[0]

        st.markdown('</div>', unsafe_allow_html=True)

        # Resumen y Botón de Inicio
        if uploaded_files:
            st.markdown(f"""
            <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="font-weight: 700; color: #818cf8; font-size: 0.88rem; margin-bottom: 4px;">Listo para Procesar</div>
                <div style="color: #cbd5e1; font-size: 0.82rem;">
                    Se crearán <strong>{len(uploaded_files)} documentos</strong> en cola con destino <strong>{target_lang_name}</strong>.
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Iniciar Traducción en Lote", type="primary", use_container_width=True):
                gemini_key = st.session_state.get("gemini_key", "").strip()
                deepl_key = st.session_state.get("deepl_key", "").strip()

                if pipeline_mode == "deepl" and not deepl_key:
                    st.error("⚠️ Ingresa tu **DeepL API Key** en la barra lateral o en la pestaña de Configuración.")
                    return

                if pipeline_mode in ["multi_agente", "gemini_directo"] and not gemini_key:
                    st.error("⚠️ Ingresa tu **Gemini API Key** en la barra lateral o en la pestaña de Configuración.")
                    return

                with st.spinner("Inicializando lote y extrayendo estructura de los artículos..."):
                    try:
                        lote_id = BatchService.create_batch(
                            nombre=batch_name,
                            idioma_origen=source_lang,
                            idioma_destino=target_lang,
                            modo_pipeline=pipeline_mode,
                            uploaded_files=uploaded_files
                        )
                        st.session_state["active_batch_id"] = lote_id
                        st.success(f"✅ ¡Lote #{lote_id} creado con éxito!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear el lote: {e}")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1.2rem; background: rgba(255, 255, 255, 0.02); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 12px; color: #94a3b8; font-size: 0.85rem;">
                💡 Sube archivos a la izquierda para habilitar el procesamiento.
            </div>
            """, unsafe_allow_html=True)
