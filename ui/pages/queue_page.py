import streamlit as st
import time
from sqlalchemy import text
from database.connection import get_db
from services.batch_service import BatchService
from services.export_service import ExportService

def render_queue_page():
    st.markdown("### 📊 Monitor de Lotes y Ejecución de Agentes")

    with get_db() as db:
        query = text("""
            SELECT id, nombre, estado, modo_pipeline, total_documentos, documentos_completados, tiempo_segundos
            FROM lotes
            ORDER BY id DESC
        """)
        rows = db.execute(query).mappings().all()
        lotes_data = [dict(r) for r in rows]

    if not lotes_data:
        st.info("No hay lotes creados aún. Ve a la pestaña **Cargar Artículos** para iniciar uno.")
        return

    # Selector de lote
    lote_options = {f"#{l['id']} - {l['nombre']} ({str(l['estado']).upper()})": l['id'] for l in lotes_data}
    selected_label = list(lote_options.keys())[0]

    if "active_batch_id" in st.session_state and st.session_state["active_batch_id"]:
        for label, l_id in lote_options.items():
            if l_id == st.session_state["active_batch_id"]:
                selected_label = label
                break

    col_sel, col_action = st.columns([3, 1])
    with col_sel:
        selected_lote_str = st.selectbox(
            "Seleccionar Lote para Monitorear",
            options=list(lote_options.keys()),
            index=list(lote_options.keys()).index(selected_label)
        )
        current_lote_id = lote_options[selected_lote_str]
        st.session_state["active_batch_id"] = current_lote_id

    # Obtener detalles del lote actual mediante SQL puro
    with get_db() as db:
        lote_res = db.execute(
            text("SELECT id, nombre, estado, modo_pipeline, total_documentos, documentos_completados, tiempo_segundos FROM lotes WHERE id = :lote_id"),
            {"lote_id": current_lote_id}
        ).mappings().first()

        if not lote_res:
            st.error("Lote no encontrado.")
            return

        lote_info = dict(lote_res)

        docs_res = db.execute(
            text("SELECT id, nombre_archivo, estado, total_palabras, total_tokens, puntuacion_calidad FROM documentos WHERE lote_id = :lote_id ORDER BY id ASC"),
            {"lote_id": current_lote_id}
        ).mappings().all()
        docs_data = [dict(d) for d in docs_res]

        logs_res = db.execute(
            text("SELECT id, agente, nivel, mensaje, fecha_creacion FROM registros_agente WHERE lote_id = :lote_id ORDER BY id DESC LIMIT 15"),
            {"lote_id": current_lote_id}
        ).mappings().all()

        logs_data = []
        for log in logs_res:
            log_dict = dict(log)
            fc = log_dict.get("fecha_creacion")
            log_dict["fecha_str"] = fc.strftime("%H:%M:%S") if hasattr(fc, "strftime") else str(fc or "")
            logs_data.append(log_dict)

    # Tarjetas de resumen
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-container">
            <div>
                <div class="metric-val">{lote_info.get('total_documentos', 0)}</div>
                <div class="metric-lbl">Total Artículos</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-container">
            <div>
                <div class="metric-val">{lote_info.get('documentos_completados', 0)}</div>
                <div class="metric-lbl">Completados</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        status_cls = f"badge-{lote_info.get('estado', 'pendiente')}"
        st.markdown(f"""
        <div class="metric-container">
            <div>
                <div style="margin-top: 5px;"><span class="status-badge {status_cls}">{lote_info.get('estado', 'pendiente')}</span></div>
                <div class="metric-lbl" style="margin-top: 8px;">Estado del Lote</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        tiempo = f"{lote_info.get('tiempo_segundos', 0.0):.1f}s" if lote_info.get('tiempo_segundos') else "En curso..."
        st.markdown(f"""
        <div class="metric-container">
            <div>
                <div class="metric-val" style="font-size: 1.4rem;">{tiempo}</div>
                <div class="metric-lbl">Tiempo de Ejecución</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Controles de Ejecución y Cancelación
    col_exec, col_cancel = st.columns([2, 1])

    with col_exec:
        btn_label = "▶️ Reanudar / Ejecutar Traducción" if lote_info.get("estado") in ["pendiente", "error", "cancelado", "en_proceso"] else "🔄 Re-ejecutar Lote"
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state["cancel_requested"] = False
            gemini_key = st.session_state.get("gemini_key", "").strip()
            deepl_key = st.session_state.get("deepl_key", "").strip()
            gemini_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
            current_mode = lote_info.get("modo_pipeline", "multi_agente")

            if current_mode == "deepl" and not deepl_key:
                st.error("⚠️ Este lote está configurado para **DeepL**. Por favor ingresa tu DeepL API Key en la barra lateral.")
                return

            if current_mode in ["multi_agente", "gemini_directo"] and not gemini_key:
                st.error("⚠️ Este lote usa **Gemini**. Configura tu Gemini API Key en la barra lateral antes de iniciar.")
                return

            progress_bar = st.progress(0.0)
            status_text = st.empty()
            log_container = st.empty()

            live_logs = []

            def on_progress(current, total, msg):
                progress_bar.progress(current / total)
                status_text.markdown(f"**Progreso:** {msg}")

            def on_log(agent, msg):
                live_logs.append(f"[{time.strftime('%H:%M:%S')}] [{agent}] {msg}")
                formatted_logs = "<br>".join(live_logs[-8:])
                log_container.markdown(f"""
                <div class="agent-console">
                    {formatted_logs}
                </div>
                """, unsafe_allow_html=True)

            def check_cancelled():
                return st.session_state.get("cancel_requested", False)

            spinner_msg = "⚡ Traduciendo artículos a alta velocidad con DeepL..." if current_mode == "deepl" else f"🧠 Agentes traduciendo concurrentemente con {gemini_model}..."

            with st.spinner(spinner_msg):
                try:
                    BatchService.process_batch(
                        lote_id=lote_info["id"],
                        gemini_api_key=gemini_key,
                        deepl_api_key=deepl_key,
                        model_name=gemini_model,
                        progress_callback=on_progress,
                        log_callback=on_log,
                        cancel_check=check_cancelled
                    )
                    if st.session_state.get("cancel_requested", False):
                        st.warning("⏹️ Procesamiento detenido por el usuario.")
                    else:
                        st.success("🎉 ¡Procesamiento del lote completado con éxito!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocurrió un error durante la ejecución: {e}")

    with col_cancel:
        if st.button("⏹️ Detener / Cancelar", type="secondary", use_container_width=True):
            st.session_state["cancel_requested"] = True
            with get_db() as db:
                db.execute(
                    text("UPDATE lotes SET estado = 'cancelado' WHERE id = :lid"),
                    {"lid": lote_info["id"]}
                )
            st.warning("⚠️ Señal de parada enviada. El lote ha sido marcado como cancelado.")
            time.sleep(0.5)
            st.rerun()

    # Tabla de Documentos
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📄 Artículos del Lote")
    doc_rows = []
    for d in docs_data:
        calidad_val = d.get('puntuacion_calidad')
        score_str = f"⭐ {calidad_val:.1f}/5.0" if calidad_val else "N/A"
        tokens_val = d.get('total_tokens')
        tokens_str = f"{tokens_val:,}" if tokens_val else "N/A"
        words_val = d.get('total_palabras')
        words_str = f"{words_val:,}" if words_val else "0"
        estado_val = d.get('estado', 'pendiente')
        status_tag = f'<span class="status-badge badge-{estado_val}">{estado_val}</span>'

        doc_rows.append({
            "ID": d["id"],
            "Artículo": d["nombre_archivo"],
            "Estado": status_tag,
            "Palabras": words_str,
            "Tokens": tokens_str,
            "Calidad": score_str
        })

    if doc_rows:
        import pandas as pd
        df = pd.DataFrame(doc_rows)
        st.markdown(
            df.to_html(escape=False, index=False, classes="table table-dark"),
            unsafe_allow_html=True
        )

    # Descarga masiva ZIP si el lote tiene documentos completados
    completed_docs = [d for d in docs_data if d.get('estado') == 'completado']
    if completed_docs or lote_info.get("estado") == "completado":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📥 Descargas Masivas del Lote")
        col_z1, col_z2, col_z3, col_z4 = st.columns(4)
        try:
            with col_z1:
                zip_name_pdf, zip_bytes_pdf = ExportService.export_batch_zip(lote_info["id"], format_type="pdf")
                st.download_button("📕 Descargar en PDF (ZIP)", data=zip_bytes_pdf, file_name=zip_name_pdf, mime="application/zip", use_container_width=True)
            with col_z2:
                zip_name, zip_bytes = ExportService.export_batch_zip(lote_info["id"], format_type="docx")
                st.download_button("📦 Descargar en Word DOCX (ZIP)", data=zip_bytes, file_name=zip_name, mime="application/zip", use_container_width=True)
            with col_z3:
                zip_name_md, zip_bytes_md = ExportService.export_batch_zip(lote_info["id"], format_type="md")
                st.download_button("📄 Descargar en Markdown (ZIP)", data=zip_bytes_md, file_name=zip_name_md, mime="application/zip", use_container_width=True)
            with col_z4:
                zip_name_txt, zip_bytes_txt = ExportService.export_batch_zip(lote_info["id"], format_type="txt")
                st.download_button("📝 Descargar en TXT (ZIP)", data=zip_bytes_txt, file_name=zip_name_txt, mime="application/zip", use_container_width=True)
        except Exception as e:
            st.error(f"Error generando exportación: {e}")

    # Consola de Registros de Agentes
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🔍 Trazabilidad y Razonamiento de Agentes (PostgreSQL)")
    if logs_data:
        log_html = ['<div class="agent-console">']
        for log in reversed(logs_data):
            cls = "log-msg"
            if log.get("nivel") == "SUCCESS": cls = "log-success"
            elif log.get("nivel") == "WARNING": cls = "log-warn"
            elif log.get("nivel") == "ERROR": cls = "log-err"
            log_html.append(f'<div class="log-line"><span class="log-time">[{log.get("fecha_str")}]</span> <span class="log-agent">[{log.get("agente")}]</span> <span class="{cls}">{log.get("mensaje")}</span></div>')
        log_html.append('</div>')
        st.markdown("\n".join(log_html), unsafe_allow_html=True)
    else:
        st.caption("No hay logs registrados para este lote todavía.")
