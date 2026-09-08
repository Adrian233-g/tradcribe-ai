import streamlit as st
import time
from sqlalchemy import text
from database.connection import get_db
from services.batch_service import BatchService
from services.export_service import ExportService

def render_queue_page():
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">
            📊 Monitor de Lotes y Ejecución en Tiempo Real
        </h2>
        <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">
            Supervisa el avance de los agentes, trazabilidad en base de datos y descarga masiva de artículos traducidos.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with get_db() as db:
        query = text("""
            SELECT id, nombre, estado, modo_pipeline, total_documentos, documentos_completados, tiempo_segundos
            FROM lotes
            ORDER BY id DESC
        """)
        rows = db.execute(query).mappings().all()
        lotes_data = [dict(r) for r in rows]

    if not lotes_data:
        st.markdown("""
        <div class="card-pro" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">📭</div>
            <h3 style="color: #f1f5f9; margin: 0 0 0.5rem 0;">No hay lotes creados todavía</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">
                Dirígete a la pestaña <strong>Cargar Artículos</strong> para crear tu primer lote de traducción.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Selector de lote
    lote_options = {f"#{l['id']} - {l['nombre']} ({str(l['estado']).upper()})": l['id'] for l in lotes_data}
    selected_label = list(lote_options.keys())[0]

    if "active_batch_id" in st.session_state and st.session_state["active_batch_id"]:
        for label, l_id in lote_options.items():
            if l_id == st.session_state["active_batch_id"]:
                selected_label = label
                break

    col_sel, col_empty = st.columns([2.5, 1.5])
    with col_sel:
        selected_lote_str = st.selectbox(
            "Lote a Monitorear:",
            options=list(lote_options.keys()),
            index=list(lote_options.keys()).index(selected_label),
            label_visibility="collapsed"
        )
        current_lote_id = lote_options[selected_lote_str]
        st.session_state["active_batch_id"] = current_lote_id

    # Obtener datos del lote actual
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
            text("SELECT id, agente, nivel, mensaje, fecha_creacion FROM registros_agente WHERE lote_id = :lote_id ORDER BY id DESC LIMIT 20"),
            {"lote_id": current_lote_id}
        ).mappings().all()

        logs_data = []
        for log in logs_res:
            log_dict = dict(log)
            fc = log_dict.get("fecha_creacion")
            log_dict["fecha_str"] = fc.strftime("%H:%M:%S") if hasattr(fc, "strftime") else str(fc or "")
            logs_data.append(log_dict)

    # 4 KPI Cards
    status_val = lote_info.get('estado', 'pendiente')
    status_cls = f"badge-{status_val}"
    pulse_dot = "pulse-dot" if status_val in ["en_proceso", "traduciendo"] else ""
    tiempo_val = f"{lote_info.get('tiempo_segundos', 0.0):.1f}s" if lote_info.get('tiempo_segundos') else ("En curso..." if status_val == "en_proceso" else "0.0s")

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-val">{lote_info.get('total_documentos', 0)}</div>
            <div class="kpi-lbl">Total Artículos</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="background: linear-gradient(135deg, #34d399 0%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {lote_info.get('documentos_completados', 0)}
            </div>
            <div class="kpi-lbl">Completados</div>
        </div>
        <div class="kpi-card">
            <div style="margin-top: 4px;">
                <span class="status-pill {status_cls}">
                    <span class="status-dot {pulse_dot}"></span>
                    {status_val}
                </span>
            </div>
            <div class="kpi-lbl" style="margin-top: 8px;">Estado del Lote</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="font-size: 1.6rem; font-family: 'JetBrains Mono', monospace;">
                {tiempo_val}
            </div>
            <div class="kpi-lbl">Tiempo Transcurrido</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Controles de Ejecución y Cancelación
    col_exec, col_cancel = st.columns([2.5, 1.2])

    with col_exec:
        btn_label = "▶️ Reanudar / Ejecutar Traducción" if lote_info.get("estado") in ["pendiente", "error", "cancelado", "en_proceso"] else "🔄 Re-ejecutar Lote Completo"
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state["cancel_requested"] = False
            gemini_key = st.session_state.get("gemini_key", "").strip()
            deepl_key = st.session_state.get("deepl_key", "").strip()
            gemini_model = st.session_state.get("gemini_model", "gemini-2.0-flash")
            current_mode = lote_info.get("modo_pipeline", "multi_agente")

            if current_mode == "deepl" and not deepl_key:
                st.error("⚠️ Este lote requiere **DeepL API Key**. Configúrala en la barra lateral.")
                return

            if current_mode in ["multi_agente", "gemini_directo"] and not gemini_key:
                st.error("⚠️ Este lote requiere **Gemini API Key**. Configúrala en la barra lateral.")
                return

            progress_bar = st.progress(0.0)
            status_text = st.empty()
            log_container = st.empty()

            live_logs = []

            def on_progress(current, total, msg):
                progress_bar.progress(current / total)
                status_text.markdown(f"**Progreso ({int(current/total*100)}%):** {msg}")

            def on_log(agent, msg):
                live_logs.append(f"[{time.strftime('%H:%M:%S')}] [{agent}] {msg}")
                formatted_logs = "<br>".join(live_logs[-8:])
                log_container.markdown(f"""
                <div class="agent-terminal-window">
                    <div class="terminal-header">
                        <div class="terminal-dots">
                            <span class="t-dot t-red"></span>
                            <span class="t-dot t-yellow"></span>
                            <span class="t-dot t-green"></span>
                        </div>
                        <span class="terminal-title">live-agent-execution</span>
                    </div>
                    <div class="agent-console">
                        {formatted_logs}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            def check_cancelled():
                return st.session_state.get("cancel_requested", False)

            spinner_msg = "⚡ Traduciendo artículos con DeepL NMT..." if current_mode == "deepl" else f"🧠 Agentes procesando concurrentemente con {gemini_model}..."

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

    # Tabla de Artículos del Lote
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card-header-title">
        <span>📄</span> Artículos en el Lote
    </div>
    """, unsafe_allow_html=True)

    if docs_data:
        table_rows = []
        for d in docs_data:
            calidad_val = d.get('puntuacion_calidad')
            score_str = f"⭐ {calidad_val:.1f} / 5.0" if calidad_val else "<span style='color:#64748b;'>N/A</span>"
            tokens_val = d.get('total_tokens')
            tokens_str = f"{tokens_val:,}" if tokens_val else "-"
            words_val = d.get('total_palabras')
            words_str = f"{words_val:,}" if words_val else "-"
            estado_val = d.get('estado', 'pendiente')
            status_tag = f'<span class="status-pill badge-{estado_val}"><span class="status-dot"></span>{estado_val}</span>'

            table_rows.append(f"""
            <tr>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #94a3b8;">#{d['id']}</td>
                <td style="font-weight: 600; color: #f8fafc;">{d['nombre_archivo']}</td>
                <td>{status_tag}</td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.84rem;">{words_str}</td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.84rem; color: #94a3b8;">{tokens_str}</td>
                <td>{score_str}</td>
            </tr>
            """)

        table_html = f"""
        <table class="modern-table">
            <thead>
                <tr>
                    <th style="width: 60px;">ID</th>
                    <th>Documento</th>
                    <th style="width: 150px;">Estado</th>
                    <th style="width: 120px;">Palabras</th>
                    <th style="width: 120px;">Tokens</th>
                    <th style="width: 140px;">Calidad</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    # Descarga Masiva ZIP
    completed_docs = [d for d in docs_data if d.get('estado') == 'completado']
    if completed_docs or lote_info.get("estado") == "completado":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card-header-title">
            <span>📦</span> Descargas Masivas del Lote
        </div>
        """, unsafe_allow_html=True)

        col_z1, col_z2, col_z3, col_z4 = st.columns(4)
        try:
            with col_z1:
                zip_name_pdf, zip_bytes_pdf = ExportService.export_batch_zip(lote_info["id"], format_type="pdf")
                st.download_button("📕 PDF Lote (.zip)", data=zip_bytes_pdf, file_name=zip_name_pdf, mime="application/zip", use_container_width=True)
            with col_z2:
                zip_name_docx, zip_bytes_docx = ExportService.export_batch_zip(lote_info["id"], format_type="docx")
                st.download_button("📄 Word DOCX (.zip)", data=zip_bytes_docx, file_name=zip_name_docx, mime="application/zip", use_container_width=True)
            with col_z3:
                zip_name_md, zip_bytes_md = ExportService.export_batch_zip(lote_info["id"], format_type="md")
                st.download_button("📝 Markdown (.zip)", data=zip_bytes_md, file_name=zip_name_md, mime="application/zip", use_container_width=True)
            with col_z4:
                zip_name_txt, zip_bytes_txt = ExportService.export_batch_zip(lote_info["id"], format_type="txt")
                st.download_button("📃 Texto Plano (.zip)", data=zip_bytes_txt, file_name=zip_name_txt, mime="application/zip", use_container_width=True)
        except Exception as e:
            st.error(f"Error generando exportación: {e}")

    # Consola de Registros de Agentes
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card-header-title">
        <span>🔍</span> Trazabilidad de Agentes (Auditoría PostgreSQL)
    </div>
    """, unsafe_allow_html=True)

    if logs_data:
        log_lines_html = []
        for log in reversed(logs_data):
            cls = "log-msg"
            if log.get("nivel") == "SUCCESS": cls = "log-success"
            elif log.get("nivel") == "WARNING": cls = "log-warn"
            elif log.get("nivel") == "ERROR": cls = "log-err"
            log_lines_html.append(f'<div class="log-line"><span class="log-time">[{log.get("fecha_str")}]</span> <span class="log-agent">[{log.get("agente")}]</span> <span class="{cls}">{log.get("mensaje")}</span></div>')

        st.markdown(f"""
        <div class="agent-terminal-window">
            <div class="terminal-header">
                <div class="terminal-dots">
                    <span class="t-dot t-red"></span>
                    <span class="t-dot t-yellow"></span>
                    <span class="t-dot t-green"></span>
                </div>
                <span class="terminal-title">postgresql-agent-logs : lote #{lote_info['id']}</span>
            </div>
            <div class="agent-console">
                {''.join(log_lines_html)}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("No hay logs registrados para este lote todavía.")
