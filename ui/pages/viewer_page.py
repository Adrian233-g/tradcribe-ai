import streamlit as st
from sqlalchemy import text
from database.connection import get_db
from services.export_service import ExportService

def render_viewer_page():
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">
            🔍 Visor Comparativo y Editor de Artículos
        </h2>
        <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">
            Inspecciona lado a lado el texto extraído vs. la traducción generada, edita directamente y descarga en cualquier formato.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with get_db() as db:
        docs_rows = db.execute(
            text("SELECT id, lote_id, nombre_archivo, estado FROM documentos ORDER BY id DESC")
        ).mappings().all()
        docs_list = [dict(d) for d in docs_rows]

    if not docs_list:
        st.markdown("""
        <div class="card-pro" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">📄</div>
            <h3 style="color: #f1f5f9; margin: 0 0 0.5rem 0;">No hay documentos procesados aún</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">
                Carga y procesa un lote para poder inspeccionar los resultados aquí.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    doc_options = {f"Doc #{d['id']}: {d['nombre_archivo']} (Lote #{d['lote_id']} • {d['estado']})": d['id'] for d in docs_list}
    selected_doc_label = st.selectbox(
        "Seleccionar artículo a inspeccionar:",
        options=list(doc_options.keys()),
        label_visibility="collapsed"
    )
    doc_id = doc_options[selected_doc_label]

    with get_db() as db:
        doc_row = db.execute(
            text("SELECT id, lote_id, nombre_archivo, contenido_original, contenido_traducido, total_palabras, total_tokens, puntuacion_calidad FROM documentos WHERE id = :doc_id"),
            {"doc_id": doc_id}
        ).mappings().first()

        if not doc_row:
            st.error("Documento no encontrado.")
            return

        doc = dict(doc_row)

        lote_row = db.execute(
            text("SELECT idioma_origen, idioma_destino FROM lotes WHERE id = :lote_id"),
            {"lote_id": doc['lote_id']}
        ).mappings().first()

        idioma_origen = str(lote_row['idioma_origen']).upper() if lote_row and 'idioma_origen' in lote_row else "EN"
        idioma_destino = str(lote_row['idioma_destino']).upper() if lote_row and 'idioma_destino' in lote_row else "ES"

        chunks_rows = db.execute(
            text("SELECT indice, contenido_original, contenido_traducido, notas_critico FROM fragmentos_documento WHERE documento_id = :doc_id ORDER BY indice ASC"),
            {"doc_id": doc_id}
        ).mappings().all()
        chunks = [dict(c) for c in chunks_rows]

    # Barra de Métricas del Documento
    calidad = f"{doc.get('puntuacion_calidad', 0.0):.1f} / 5.0" if doc.get('puntuacion_calidad') else "N/A"
    
    st.markdown(f"""
    <div class="kpi-container" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 1.25rem;">
        <div class="kpi-card">
            <div class="kpi-val">{doc.get('total_palabras', 0):,}</div>
            <div class="kpi-lbl">Palabras Traducidas</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #94a3b8;">{doc.get('total_tokens', 0):,}</div>
            <div class="kpi-lbl">Tokens Consumidos</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {calidad}
            </div>
            <div class="kpi-lbl">Puntuación Calidad</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val">{len(chunks)}</div>
            <div class="kpi-lbl">Fragmentos Semánticos</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Vista lado a lado: Original vs Traducido
    col_orig, col_trans = st.columns(2, gap="medium")

    with col_orig:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 700; color: #f1f5f9; font-size: 0.95rem;">
                📄 Texto Original
            </span>
            <span style="font-size: 0.78rem; font-weight: 700; background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 6px; color: #94a3b8;">
                {idioma_origen}
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.text_area(
            "Texto Original Extraído",
            value=doc.get('contenido_original') or "",
            height=490,
            disabled=True,
            key=f"orig_{doc['id']}",
            label_visibility="collapsed"
        )

    with col_trans:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 700; color: #f1f5f9; font-size: 0.95rem;">
                🌐 Traducción Generada (Editable)
            </span>
            <span style="font-size: 0.78rem; font-weight: 700; background: rgba(99,102,241,0.2); padding: 2px 8px; border-radius: 6px; color: #818cf8; border: 1px solid rgba(99,102,241,0.3);">
                {idioma_destino}
            </span>
        </div>
        """, unsafe_allow_html=True)
        edited_translation = st.text_area(
            "Traducción Generada",
            value=doc.get('contenido_traducido') or "Aún no traducido.",
            height=490,
            key=f"trans_{doc['id']}",
            label_visibility="collapsed"
        )

        if st.button("💾 Guardar Cambios en PostgreSQL", use_container_width=True, type="secondary"):
            with get_db() as db:
                words = len(edited_translation.split())
                db.execute(
                    text("UPDATE documentos SET contenido_traducido = :trans, total_palabras = :words WHERE id = :doc_id"),
                    {"trans": edited_translation, "words": words, "doc_id": doc_id}
                )
            st.success("¡Traducción actualizada y persistida con éxito!")

    # Botones de Exportación Individual
    if doc.get('contenido_traducido'):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card-header-title">
            <span>📥</span> Exportar este Artículo
        </div>
        """, unsafe_allow_html=True)

        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        with col_d1:
            fn_pdf, b_pdf = ExportService.get_document_export(doc['id'], "pdf")
            st.download_button("📕 Descargar PDF (.pdf)", data=b_pdf, file_name=fn_pdf, mime="application/pdf", use_container_width=True)
        with col_d2:
            fn_docx, b_docx = ExportService.get_document_export(doc['id'], "docx")
            st.download_button("📄 Descargar Word (.docx)", data=b_docx, file_name=fn_docx, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with col_d3:
            fn_md, b_md = ExportService.get_document_export(doc['id'], "md")
            st.download_button("📝 Descargar Markdown (.md)", data=b_md, file_name=fn_md, mime="text/markdown", use_container_width=True)
        with col_d4:
            fn_txt, b_txt = ExportService.get_document_export(doc['id'], "txt")
            st.download_button("📃 Descargar Texto (.txt)", data=b_txt, file_name=fn_txt, mime="text/plain", use_container_width=True)

    # Detalle por Fragmentos y Auditoría de Agentes
    if chunks:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"🧩 Auditoría Detallada por Fragmentos ({len(chunks)} Chunks Semánticos)"):
            for chunk in chunks:
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="font-weight: 700; color: #818cf8; font-size: 0.9rem;">Chunk #{chunk.get('indice', 0) + 1}</span>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Texto Original Extraído:")
                    orig_c = chunk.get('contenido_original', '')
                    st.code(orig_c[:350] + ("..." if len(orig_c) > 350 else ""), language="markdown")
                with c2:
                    st.caption("Traducción Generada:")
                    trans_c = chunk.get('contenido_traducido', '')
                    st.code(trans_c[:350] + ("..." if len(trans_c) > 350 else ""), language="markdown")

                if chunk.get('notas_critico'):
                    st.info(f"🧐 **Notas del Agente Crítico:** {chunk.get('notas_critico')}")
                st.markdown("<hr style='border: none; height: 1px; background: rgba(255,255,255,0.06); margin: 0.75rem 0;'>", unsafe_allow_html=True)
