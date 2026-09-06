<p align="center">
  <h1 align="center">🌐 Tradcribe AI</h1>
  <p align="center">
    <strong>Sistema de Traducción de Artículos Científicos con Multi-Agentes IA</strong>
  </p>
  <p align="center">
    Pipeline híbrido DeepL + Gemini · Exportación PDF/DOCX de alta fidelidad · PostgreSQL
  </p>
</p>

---

## 📋 Descripción

**Tradcribe AI** es una aplicación web construida con Streamlit que permite traducir artículos científicos y técnicos en lote, preservando la estructura, formato y terminología especializada del documento original.

### ✨ Características Principales

- 🔄 **Doble Motor de Traducción:** DeepL (ultra-rápido) y Gemini (alta calidad multi-agente)
- 📄 **Extracción Inteligente de PDFs:** Detecta encabezados, negritas y jerarquía por tamaño de fuente usando `pdfminer.six`
- 📕 **Exportación de Alta Fidelidad:** PDF y DOCX con tipografía académica (Times New Roman, A4, texto justificado)
- 🧠 **Pipeline Multi-Agente:** Glosario → Traductor → Crítico (con auditoría de calidad 1-5)
- 📖 **Glosario Técnico:** Base de datos de términos especializados para consistencia terminológica
- 📊 **Monitor de Lotes:** Seguimiento en tiempo real del progreso de traducción
- 🔍 **Visor Comparativo:** Vista lado a lado Original vs Traducido con editor inline
- 💾 **PostgreSQL:** Persistencia completa de documentos, fragmentos y logs de agentes

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                   │
│  Upload · Monitor · Visor · Glosario · Config   │
├─────────────────────────────────────────────────┤
│              Pipeline de Traducción              │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Glosario │→ │ Traductor │→ │   Crítico    │  │
│  │  Agent   │  │  (Gemini/ │  │  (Auditor)   │  │
│  │          │  │   DeepL)  │  │              │  │
│  └──────────┘  └───────────┘  └──────────────┘  │
├─────────────────────────────────────────────────┤
│   Parsers                  │    Exportadores     │
│  ┌──────────────────┐      │  ┌───────────────┐  │
│  │ PDF (pdfminer)   │      │  │ PDF (reportlab)│ │
│  │ DOCX (python-docx│      │  │ DOCX          │  │
│  │ TXT/MD           │      │  │ MD / TXT      │  │
│  └──────────────────┘      │  └───────────────┘  │
├─────────────────────────────────────────────────┤
│              PostgreSQL Database                 │
│  Lotes · Documentos · Fragmentos · Glosario     │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Instalación

### Prerrequisitos

- **Python** 3.10+
- **PostgreSQL** 12+
- **API Key** de [Gemini](https://aistudio.google.com/) y/o [DeepL](https://www.deepl.com/pro-api)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/Tradcribe.git
cd Tradcribe

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de BD y API keys

# 5. Ejecutar
streamlit run app.py
```

---

## ⚙️ Configuración

Copia `.env.example` a `.env` y configura:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DB_HOST` | Host de PostgreSQL | `localhost` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `DB_USER` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña de PostgreSQL | `mi_password` |
| `DB_NAME` | Nombre de la base de datos | `tradcribe_db` |
| `GEMINI_API_KEY` | API Key de Google Gemini | `AIza...` |
| `GEMINI_MODEL` | Modelo de Gemini a usar | `gemini-2.0-flash` |
| `DEEPL_API_KEY` | API Key de DeepL | `abcd-1234:fx` |
| `AGENT_MAX_CHUNK_SIZE` | Tamaño máximo de fragmento | `8000` |
| `AGENT_CRITIC_ENABLED` | Activar agente crítico | `true` |
| `AGENT_TEMPERATURE` | Temperatura del LLM | `0.2` |

---

## 📁 Estructura del Proyecto

```
Tradcribe/
├── app.py                    # Punto de entrada Streamlit
├── config.py                 # Configuración centralizada
├── requirements.txt          # Dependencias Python
├── .env.example              # Plantilla de variables de entorno
│
├── agents/                   # Pipeline multi-agente
│   ├── agent_pipeline.py     # Orquestador principal
│   ├── translator_agent.py   # Agente traductor (Gemini)
│   ├── critic_agent.py       # Agente crítico/auditor
│   ├── glossary_agent.py     # Agente de glosario técnico
│   ├── deepl_translator.py   # Motor DeepL ultra-rápido
│   ├── gemini_client.py      # Cliente Gemini con retry/backoff
│   ├── parser_agent.py       # Segmentador inteligente (chunking)
│   ├── fallback_translators.py # Traductores de respaldo
│   └── state.py              # Estado del documento
│
├── parsers/                  # Parsers y generadores
│   ├── pdf_parser.py         # Extracción inteligente PDF (pdfminer.six)
│   ├── pdf_generator.py      # Generador PDF académico (reportlab)
│   ├── docx_parser.py        # Parser/generador DOCX
│   └── text_parser.py        # Parser de texto plano
│
├── database/                 # Capa de persistencia
│   ├── connection.py         # Conexión PostgreSQL (SQLAlchemy)
│   ├── models.py             # Modelos ORM
│   └── migrations.py         # Inicialización y migraciones
│
├── services/                 # Servicios de negocio
│   ├── export_service.py     # Exportación PDF/DOCX/ZIP
│   └── batch_service.py      # Procesamiento en lote
│
├── ui/                       # Interfaz de usuario Streamlit
│   ├── components.py         # Componentes reutilizables
│   ├── styles.py             # CSS personalizado
│   └── pages/
│       ├── upload_page.py    # Carga de artículos
│       ├── queue_page.py     # Monitor de lotes
│       ├── viewer_page.py    # Visor comparativo
│       ├── glossary_page.py  # Gestión de glosario
│       └── settings_page.py  # Configuración
│
├── samples/                  # Artículos de ejemplo
│   ├── article_1_ai_advances.md
│   └── article_2_quantum_computing.txt
│
└── test_system.py            # Suite de pruebas
```

---

## 🔧 Motores de Traducción

| Motor | Velocidad | Calidad | Costo | Uso Recomendado |
|---|---|---|---|---|
| **DeepL** | ⚡ Ultra-rápido (~100ms/chunk) | ★★★★☆ | API gratuita/Pro | Traducciones rápidas de alto volumen |
| **Gemini Multi-Agente** | 🔄 Moderado (~3-5s/chunk) | ★★★★★ | API gratuita | Máxima calidad con auditoría |
| **Gemini Directo** | 🔄 Rápido (~2s/chunk) | ★★★★☆ | API gratuita | Balance velocidad/calidad |

---

## 📄 Formatos de Exportación

| Formato | Características |
|---|---|
| **PDF** | A4, Times New Roman, texto justificado, título centrado, tablas profesionales |
| **DOCX** | A4, Times New Roman 11pt, espaciado 1.15, headings con colores jerárquicos |
| **Markdown** | Formato raw con toda la estructura preservada |
| **TXT** | Texto plano para procesamiento posterior |

---

## 🧪 Tests

```bash
python test_system.py
```

Valida: base de datos, glosario, chunking, exportación DOCX/PDF, motores DeepL/Gemini.

---

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

<p align="center">
  Desarrollado con ❤️ por <strong>Adrian Sistemas</strong>
</p>
