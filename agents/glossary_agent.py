import re
from typing import Dict
from database.connection import get_db
from database.models import Glosario

class GlossaryAgent:
    """Detecta términos clave y consulta la base de datos de PostgreSQL para forzar consistencia terminológica."""

    @staticmethod
    def find_glossary_terms(text: str, source_lang: str = "en", target_lang: str = "es") -> Dict[str, str]:
        """Busca términos del glosario que aparezcan en el fragmento de texto."""
        matches = {}
        try:
            with get_db() as db:
                terms = db.query(Glosario).filter(
                    Glosario.idioma_origen == source_lang,
                    Glosario.idioma_destino == target_lang
                ).all()

                text_lower = text.lower()
                for t in terms:
                    # Búsqueda por palabra completa
                    pattern = r'\b' + re.escape(t.termino_origen.lower()) + r'\b'
                    if re.search(pattern, text_lower):
                        matches[t.termino_origen] = t.termino_destino
        except Exception as e:
            # Si hay algún problema momentáneo con la BD, continúa sin bloquear
            pass

        return matches

    @staticmethod
    def format_glossary_prompt(glossary_matches: Dict[str, str]) -> str:
        """Formatea los términos encontrados como directrices estrictas para el LLM."""
        if not glossary_matches:
            return ""

        prompt_lines = ["\n[GLOSARIO OBLIGATORIO DE TÉRMINOS TÉCNICOS / CIENTÍFICOS]:"]
        for orig, dest in glossary_matches.items():
            prompt_lines.append(f'- "{orig}" DEBE traducirse obligatoriamente como: "{dest}"')
        prompt_lines.append("Asegura mantener la consistencia estricta de estos términos en todo el fragmento.\n")
        return "\n".join(prompt_lines)
