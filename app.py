# Tradcribe AI - Versión 1.0.5 (Stop Button & Optimized Speed)
import sys
import importlib
import streamlit as st

# Forzar recarga de módulos del proyecto para evitar código cacheado en memoria
for mod_name in list(sys.modules.keys()):
    if any(mod_name.startswith(p) for p in ["database", "agents", "parsers", "services", "ui"]):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

from database.migrations import initialize_database
from ui.styles import apply_custom_styles
from ui.components import render_header, render_sidebar
from ui.pages.upload_page import render_upload_page
from ui.pages.queue_page import render_queue_page
from ui.pages.viewer_page import render_viewer_page
from ui.pages.glossary_page import render_glossary_page
from ui.pages.settings_page import render_settings_page

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Tradcribe AI - Traducción de Artículos en Lote con Multi-Agentes",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos PostgreSQL y tablas al arrancar
try:
    initialize_database()
except Exception as e:
    st.error(f"Aviso de Base de Datos: {e}")

# Aplicar estilos CSS personalizados
apply_custom_styles()

# Renderizar Encabezado y Barra Lateral
render_header()
render_sidebar()

# Navegación por pestañas principales
tabs = st.tabs([
    "📤 Cargar Artículos",
    "📊 Monitor de Lotes",
    "🔍 Visor Comparativo",
    "📖 Glosario Técnico",
    "⚙️ Configuración"
])

with tabs[0]:
    render_upload_page()

with tabs[1]:
    render_queue_page()

with tabs[2]:
    render_viewer_page()

with tabs[3]:
    render_glossary_page()

with tabs[4]:
    render_settings_page()
