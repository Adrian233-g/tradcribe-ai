import re
from typing import Tuple, Dict, Any
from config import Config
from agents.gemini_client import GeminiClient

class CriticAgent:
    """Agente de Revisión, Control de Calidad y Refinamiento Estilístico."""

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL

    def review_and_refine(
        self,
        original_chunk: str,
        draft_translation: str,
        source_lang: str,
        target_lang: str,
        glossary_matches: Dict[str, str] = None
    ) -> Tuple[str, str, float, int]:
        """Revisa la traducción borrador, detecta errores o inconsistencias y genera la versión final pulida."""
        if not self.api_key:
            return draft_translation, "Revisión omitida (sin API Key)", 4.5, 0

        glossary_note = ""
        if glossary_matches:
            glossary_note = "Términos obligatorios que deben respetarse:\n" + "\n".join(
                [f"- {k} => {v}" for k, v in glossary_matches.items()]
            )

        prompt = f"""Eres un Editor y Revisor de Publicaciones Científicas de élite.
Tu misión es auditar y perfeccionar la traducción de un fragmento de artículo académico ({source_lang} -> {target_lang}).

DOCUMENTO ORIGINAL:
\"\"\"
{original_chunk}
\"\"\"

TRADUCCIÓN BORRADOR RECIBIDA:
\"\"\"
{draft_translation}
\"\"\"

{glossary_note}

CRITERIOS DE REVISIÓN:
1. Exactitud conceptual: No debe haber omisiones ni adiciones de ideas.
2. Naturalidad y fluidez académica en el idioma destino ({target_lang}).
3. Preservación absoluta del formato Markdown, tablas, listas y fórmulas.
4. Cumplimiento estricto del glosario técnico.

RESPONDE EN EL SIGUIENTE FORMATO EXACTO:
---PUNTUACION---
[Calificación de 1.0 a 5.0, ej: 4.8]
---FEEDBACK---
[Breve análisis de correcciones realizadas o confirmación de calidad]
---TRADUCCION_PULIDA---
[Texto final corregido y pulido, sin introducciones adicionales]"""

        try:
            content = GeminiClient.generate_text(
                prompt=prompt,
                api_key=self.api_key,
                preferred_model=self.model_name,
                temperature=0.1
            )

            score = 4.8
            feedback = "Revisión completada satisfactoriamente."
            polished_text = draft_translation

            score_match = re.search(r'---PUNTUACION---\s*([\d\.]+)', content)
            if score_match:
                try:
                    score = float(score_match.group(1))
                except ValueError:
                    score = 4.5

            feedback_match = re.search(r'---FEEDBACK---\s*(.*?)\s*---TRADUCCION_PULIDA---', content, re.DOTALL)
            if feedback_match:
                feedback = feedback_match.group(1).strip()

            polished_match = re.search(r'---TRADUCCION_PULIDA---\s*(.*)', content, re.DOTALL)
            if polished_match:
                polished_text = polished_match.group(1).strip()

            tokens = (len(prompt) + len(content)) // 4
            return polished_text, feedback, score, tokens
        except Exception as e:
            return draft_translation, f"Revisión automática omitida: {e}", 4.5, 0
