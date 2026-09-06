import streamlit as st
from sqlalchemy import text
from database.connection import get_db
from services.export_service import ExportService

def render_viewer_page():
    st.markdown("### 🔍 Visor Comparativo y Editor de Artículos")

    with get_db() as db:
        docs_rows = db.execute(
            text("SELECT id, lote_id, nombre_archivo, estado FROM documentos ORDER BY id DESC")
        ).mappings().all()
        docs_list = [dict(d) for d in docs_rows]

    if not docs_list:
        st.info("No hay documentos procesados aún.")
        return

    doc_options = {f"Doc #{d['id']}: {d['nombre_archivo']} (Lote #{d['lote_id']} - {d['estado']})": d['id'] for d in docs_list}
    selected_doc_label = st.selectbox("Selecciona un artículo para inspeccionar:", options=list(doc_options.keys()))
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
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Palabras Traducidas", f"{doc.get('total_palabras', 0):,}")
    with col_m2:
        st.metric("Tokens Invertidos", f"{doc.get('total_tokens', 0):,}")
    with col_m3:
        calidad = f"{doc.get('puntuacion_calidad', 0.0):.1f} / 5.0" if doc.get('puntuacion_calidad') else "N/A"
        st.metric("Calidad de Traducción", calidad)
    with col_m4:
        st.metric("Fragmentos Semánticos", len(chunks))

    st.markdown("<br>", unsafe_allow_html=True)

    # Vista lado a lado: Original vs Traducido
    col_orig, col_trans = st.columns(2)

    with col_orig:
        st.markdown(f"#### 📄 Original ({idioma_origen})")
        st.text_area(
            "Texto Original Extraído",
            value=doc.get('contenido_original') or "",
            height=480,
            disabled=True,
            key=f"orig_{doc['id']}"
        )

    with col_trans:
        st.markdown(f"#### 🌐 Traducido ({idioma_destino}) - Editable")
        edited_translation = st.text_area(
            "Traducción Generada por Agentes",
            value=doc.get('contenido_traducido') or "Aún no traducido.",
            height=480,
            key=f"trans_{doc['id']}"
        )

        col_save, col_exp = st.columns([1, 1])
        with col_save:
            if st.button("💾 Guardar Cambios en BD", use_container_width=True):
                with get_db() as db:
                    words = len(edited_translation.split())
                    db.execute(
                        text("UPDATE documentos SET contenido_traducido = :trans, total_palabras = :words WHERE id = :doc_id"),
                        {"trans": edited_translation, "words": words, "doc_id": doc_id}
                    )
                st.success("¡Traducción actualizada y persistida en PostgreSQL!")

    # Botones de Exportación Individual
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📥 Exportar este Artículo")
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    if doc.get('contenido_traducido'):
        with col_d1:
            fn_pdf, b_pdf = ExportService.get_document_export(doc['id'], "pdf")
            st.download_button("📕 Descargar en PDF (.pdf)", data=b_pdf, file_name=fn_pdf, mime="application/pdf", use_container_width=True)
        with col_d2:
            fn_docx, b_docx = ExportService.get_document_export(doc['id'], "docx")
            st.download_button("📄 Descargar en Word (.docx)", data=b_docx, file_name=fn_docx, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with col_d3:
            fn_md, b_md = ExportService.get_document_export(doc['id'], "md")
            st.download_button("📝 Descargar en Markdown (.md)", data=b_md, file_name=fn_md, mime="text/markdown", use_container_width=True)
        with col_d4:
            fn_txt, b_txt = ExportService.get_document_export(doc['id'], "txt")
            st.download_button("📃 Descargar en Texto (.txt)", data=b_txt, file_name=fn_txt, mime="text/plain", use_container_width=True)

    # Detalle por Fragmentos y Auditoría de Agentes
    if chunks:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"🧩 Auditoría Detallada por Fragmentos ({len(chunks)} Chunks)"):
            for chunk in chunks:
                st.markdown(f"**Chunk #{chunk.get('indice', 0) + 1}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Texto Original:")
                    orig_c = chunk.get('contenido_original', '')
                    st.code(orig_c[:300] + ("..." if len(orig_c) > 300 else ""), language="markdown")
                with c2:
                    st.caption("Traducción Pulida:")
                    trans_c = chunk.get('contenido_traducido', '')
                    st.code(trans_c[:300] + ("..." if len(trans_c) > 300 else ""), language="markdown")

                if chunk.get('notas_critico'):
                    st.info(f"🧐 **Notas del Agente Crítico:** {chunk.get('notas_critico')}")
                st.markdown("---")
