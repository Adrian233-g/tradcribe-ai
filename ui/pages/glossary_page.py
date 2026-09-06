import streamlit as st
import pandas as pd
from services.glossary_service import GlossaryService

def render_glossary_page():
    st.markdown("### 📖 Glosario Técnico y Memoria Terminológica")
    st.write("Gestiona la base de datos de términos científicos y técnicos en PostgreSQL para asegurar coherencia entre todos los artículos.")

    tab_view, tab_add, tab_import = st.tabs(["📚 Explorar Glosario", "➕ Agregar Término", "📥 Importación Masiva (CSV)"])

    with tab_view:
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            dominio_filtro = st.selectbox("Filtrar por Dominio", options=["Todos", "General", "Inteligencia Artificial", "Académico", "Ingeniería", "Medicina"])
        with col_f2:
            search_query = st.text_input("🔍 Buscar término en inglés o español...", placeholder="ej: Benchmark, Machine Learning...")

        terms = GlossaryService.get_all(dominio=dominio_filtro, search=search_query)

        if terms:
            data = [{
                "ID": t["id"],
                "Término Origen (EN)": t["termino_origen"],
                "Traducción Obligatoria (ES)": t["termino_destino"],
                "Dominio": t["dominio"],
                "Notas": t["notas"] or ""
            } for t in terms]

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Selector para eliminar término
            st.markdown("---")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                term_to_del = st.selectbox("Seleccionar término para eliminar:", options=[f"#{t['id']} - {t['termino_origen']} -> {t['termino_destino']}" for t in terms])
            with col_del2:
                if st.button("🗑️ Eliminar Término", type="secondary", use_container_width=True):
                    term_id = int(term_to_del.split(" - ")[0].replace("#", ""))
                    GlossaryService.delete_term(term_id)
                    st.success("Término eliminado.")
                    st.rerun()
        else:
            st.info("No se encontraron términos con los filtros aplicados.")

    with tab_add:
        st.markdown("#### Registrar Nuevo Término Obligatorio")
        with st.form("form_nuevo_termino"):
            c1, c2 = st.columns(2)
            with c1:
                orig = st.text_input("Término en Idioma Origen (ej: Few-shot learning)")
                dom = st.selectbox("Dominio de Aplicación", ["General", "Inteligencia Artificial", "Académico", "Ingeniería", "Medicina", "Física", "Economía"])
            with c2:
                dest = st.text_input("Traducción Obligatoria (ej: Aprendizaje con pocos ejemplos)")
                notas = st.text_area("Contexto o Reglas Específicas (Opcional)", height=68)

            submitted = st.form_submit_button("💾 Guardar en Glosario de PostgreSQL", type="primary")
            if submitted:
                if not orig or not dest:
                    st.error("Por favor completa tanto el término origen como la traducción.")
                else:
                    GlossaryService.add_term(
                        termino_origen=orig,
                        termino_destino=dest,
                        dominio=dom,
                        notas=notas
                    )
                    st.success(f"¡Término '{orig}' añadido con éxito!")
                    st.rerun()

    with tab_import:
        st.markdown("#### Importar Glosario desde CSV")
        st.write("El archivo CSV debe incluir columnas como: `termino_origen, termino_destino, dominio, notas`")

        uploaded_csv = st.file_uploader("Selecciona archivo CSV", type=["csv"])
        if uploaded_csv:
            csv_str = uploaded_csv.getvalue().decode("utf-8", errors="replace")
            if st.button("📥 Procesar e Importar CSV"):
                try:
                    count = GlossaryService.import_csv(csv_str)
                    st.success(f"¡Se importaron {count} términos al glosario de PostgreSQL!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al importar CSV: {e}")
