import streamlit as st

def apply_custom_styles():
    """Aplica un sistema de diseño CSS moderno, premium y altamente profesional a Streamlit."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ==========================================================================
       VARIABLES Y FUENTES GLOBALES
       ========================================================================== */
    :root {
        --bg-main: #0b0f19;
        --bg-card: rgba(17, 24, 39, 0.75);
        --border-card: rgba(255, 255, 255, 0.08);
        --accent-primary: #6366f1;
        --accent-glow: rgba(99, 102, 241, 0.25);
        --accent-cyan: #38bdf8;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: var(--bg-main);
        color: var(--text-main);
    }

    /* ==========================================================================
       LAYOUT PRINCIPAL Y CONTENEDOR
       ========================================================================== */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }

    /* Ocultar barra superior genérica de Streamlit para un look app nativa */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ==========================================================================
       TARJETAS GLASSMORPHISM Y PANELES
       ========================================================================== */
    .card-pro {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 1.25rem;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }

    .card-pro:hover {
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.5), 0 0 20px -2px var(--accent-glow);
        transform: translateY(-2px);
    }

    .card-header-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.75rem;
    }

    /* Tarjeta Compacta para Archivos */
    .file-chip {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 0.65rem 1rem;
        margin-bottom: 0.5rem;
        transition: background 0.2s ease;
    }
    .file-chip:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* ==========================================================================
       KPI & MÉTRICAS MODERNAS
       ========================================================================== */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .kpi-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        position: relative;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #6366f1, #38bdf8);
        border-radius: 14px 14px 0 0;
    }

    .kpi-val {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.2;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }

    .kpi-lbl {
        font-size: 0.82rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        margin-top: 0.4rem;
    }

    /* ==========================================================================
       BADGES Y ESTADOS VIVOS CON PULSO
       ========================================================================== */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }

    .pulse-dot {
        animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
    }

    .badge-completado {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-completado .status-dot { background: #34d399; }

    .badge-en_proceso, .badge-traduciendo {
        background: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }
    .badge-en_proceso .status-dot { background: #818cf8; }

    .badge-pendiente {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-pendiente .status-dot { background: #fbbf24; }

    .badge-error {
        background: rgba(244, 63, 94, 0.12);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .badge-error .status-dot { background: #fb7185; }

    .badge-cancelado {
        background: rgba(148, 163, 184, 0.12);
        color: #cbd5e1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }

    /* ==========================================================================
       CONSOLA / TERMINAL DE REGISTROS DE AGENTES
       ========================================================================== */
    .agent-terminal-window {
        background: #080c14;
        border: 1px solid #1e293b;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
        margin-top: 0.8rem;
    }

    .terminal-header {
        background: #0f172a;
        padding: 0.6rem 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #1e293b;
    }

    .terminal-dots {
        display: flex;
        gap: 6px;
    }

    .t-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .t-red { background: #ef4444; }
    .t-yellow { background: #f59e0b; }
    .t-green { background: #10b981; }

    .terminal-title {
        font-size: 0.76rem;
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        font-weight: 500;
    }

    .agent-console {
        background: #080c14;
        color: #e2e8f0;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.82rem;
        padding: 1.2rem;
        max-height: 320px;
        overflow-y: auto;
        line-height: 1.6;
    }

    .log-line {
        margin-bottom: 0.3rem;
        word-break: break-word;
    }
    .log-time { color: #64748b; font-size: 0.78rem; }
    .log-agent { color: #38bdf8; font-weight: 600; }
    .log-msg { color: #f1f5f9; }
    .log-success { color: #4ade80; }
    .log-warn { color: #fbbf24; }
    .log-err { color: #f87171; }

    /* ==========================================================================
       PESTAÑAS DE STREAMLIT (ST.TABS)
       ========================================================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.7);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.9rem;
        border: none !important;
        background-color: transparent;
        padding: 0 16px;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc;
        background-color: rgba(255, 255, 255, 0.04);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(129, 140, 248, 0.25) 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }

    /* ==========================================================================
       BOTONES Y CONTROLES STREAMLIT
       ========================================================================== */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(165, 180, 252, 0.3) !important;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    }

    .stButton > button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.6) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: rgba(51, 65, 85, 0.8) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* ==========================================================================
       TABLAS Y DATAFRAMES
       ========================================================================== */
    .modern-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: rgba(15, 23, 42, 0.5);
    }
    .modern-table th {
        background: rgba(30, 41, 59, 0.8);
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        padding: 0.85rem 1.1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        text-align: left;
    }
    .modern-table td {
        padding: 0.85rem 1.1rem;
        color: #e2e8f0;
        font-size: 0.88rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .modern-table tr:last-child td {
        border-bottom: none;
    }
    .modern-table tr:hover td {
        background: rgba(255, 255, 255, 0.025);
    }

    /* ==========================================================================
       SCROLLBARS ESTILIZADAS
       ========================================================================== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.6);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.25);
    }
    </style>
    """, unsafe_allow_html=True)
