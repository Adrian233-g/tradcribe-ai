import streamlit as st

def apply_custom_styles():
    """Aplica estilos CSS refinados, modernos y profesionales a la aplicación Streamlit."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Fondo y estructura general */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1350px;
    }

    /* Tarjetas estilo Glassmorphism */
    .card-dashboard {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-bottom: 1.2rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-dashboard:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.3);
    }

    /* Badges de estado */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-completado {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-en_proceso, .badge-traduciendo {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-pendiente {
        background: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    .badge-error {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-agent {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    /* Métricas destacadas */
    .metric-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 500;
    }

    /* Visor lado a lado */
    .viewer-panel {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem;
        height: 520px;
        overflow-y: auto;
    }

    /* Consola de logs de agentes */
    .agent-console {
        background: #090d16;
        color: #e2e8f0;
        font-family: 'Fira Code', monospace;
        font-size: 0.82rem;
        border-radius: 10px;
        padding: 1rem;
        max-height: 280px;
        overflow-y: auto;
        border: 1px solid #1e293b;
    }
    .log-line {
        margin-bottom: 0.35rem;
        line-height: 1.4;
    }
    .log-time { color: #64748b; }
    .log-agent { color: #38bdf8; font-weight: 600; }
    .log-msg { color: #f1f5f9; }
    .log-success { color: #4ade80; }
    .log-warn { color: #fbbf24; }
    .log-err { color: #f87171; }
    </style>
    """, unsafe_allow_html=True)
