import streamlit as st
import pandas as pd
from services.glossary_service import GlossaryService

def render_glossary_page():
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">
            📖 Glosario Técnico y Memoria Terminológica
        </h2>
        <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">
            Define reglas y traducciones obligatorias para términos científicos o técnicos almacenados en PostgreSQL.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_view, tab_add, tab_import = st.tabs(["📚 Explorar Términos", "➕ Agregar Término", "📥 Importación Masiva (CSV)"])

    with tab_view:
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            dominio_filtro = st.selectbox(
                "Filtrar por Dominio",
                options=["Todos", "General", "Inteligencia Artificial", "Académico", "Ingeniería", "Medicina", "Física", "Economía"]
            )
        with col_f2:
            search_query = st.text_input("🔍 Buscar término:", placeholder="ej: Few-shot, Benchmark, Quantum...")

        terms = GlossaryService.get_all(dominio=dominio_filtro, search=search_query)

        if terms:
            # Resumen
            st.markdown(f"""
            <div style="display: flex; gap: 1rem; margin: 0.75rem 0;">
                <span style="font-size: 0.82rem; background: rgba(99,102,241,0.12); color: #818cf8; padding: 4px 10px; border-radius: 8px; border: 1px solid rgba(99,102,241,0.25);">
                    Total: <strong>{len(terms)}</strong> términos
                </span>
            </div>
            """, unsafe_allow_html=True)

            data = [{
                "ID": f"#{t['id']}",
                "Término Origen (EN)": t["termino_origen"],
                "Traducción Obligatoria (ES)": t["termino_destino"],
                "Dominio": t["dominio"],
                "Notas / Reglas": t["notas"] or "-"
            } for t in terms]

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Selector para eliminar término
            st.markdown("<br>", unsafe_allow_html=True)
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                term_to_del = st.selectbox(
                    "Eliminar término:",
                    options=[f"#{t['id']} - {t['termino_origen']} ➔ {t['termino_destino']}" for t in terms],
                    label_visibility="collapsed"
                )
            with col_del2:
                if st.button("🗑️ Eliminar", type="secondary", use_container_width=True):
                    term_id = int(term_to_del.split(" - ")[0].replace("#", ""))
                    GlossaryService.delete_term(term_id)
                    st.success("Término eliminado del glosario.")
                    st.rerun()
        else:
            st.info("No se encontraron términos para la búsqueda aplicada.")

    with tab_add:
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>➕</span> Registrar Término Obligatorio
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_nuevo_termino"):
            c1, c2 = st.columns(2)
            with c1:
                orig = st.text_input("Término en Idioma Origen (ej: Zero-shot prompting)")
                dom = st.selectbox("Dominio de Aplicación", ["General", "Inteligencia Artificial", "Académico", "Ingeniería", "Medicina", "Física", "Economía"])
            with c2:
                dest = st.text_input("Traducción Obligatoria (ej: Inducción sin ejemplos previos)")
                notas = st.text_area("Contexto o Instrucciones para Agentes (Opcional)", height=68)

            submitted = st.form_submit_button("💾 Guardar en PostgreSQL", type="primary")
            if submitted:
                if not orig or not dest:
                    st.error("Completa tanto el término origen como la traducción obligatoria.")
                else:
                    GlossaryService.add_term(
                        termino_origen=orig,
                        termino_destino=dest,
                        dominio=dom,
                        notas=notas
                    )
                    st.success(f"¡Término '{orig}' guardado con éxito!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_import:
        st.markdown("""
        <div class="card-pro">
            <div class="card-header-title">
                <span>📥</span> Importar Glosario Masivo (CSV)
            </div>
            <p style="color: #94a3b8; font-size: 0.88rem;">
                Sube un archivo CSV con las columnas: <code>termino_origen, termino_destino, dominio, notas</code>
            </p>
        """, unsafe_allow_html=True)

        uploaded_csv = st.file_uploader("Selecciona archivo CSV", type=["csv"], label_visibility="collapsed")
        if uploaded_csv:
            csv_str = uploaded_csv.getvalue().decode("utf-8", errors="replace")
            if st.button("📥 Procesar e Importar al Glosario", type="primary"):
                try:
                    count = GlossaryService.import_csv(csv_str)
                    st.success(f"¡Se importaron {count} términos al glosario de PostgreSQL!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al importar CSV: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
