import os
from typing import Tuple, Dict, Any
from config import Config
from agents.gemini_client import GeminiClient

class SeniorTranslatorAgent:
    """Agente de Traducción Especializado con Google Gemini."""

    def __init__(self, api_key: str = None, model_name: str = None, temperature: float = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL
        self.temperature = temperature if temperature is not None else Config.AGENT_TEMPERATURE

    def translate_chunk(
        self,
        chunk_text: str,
        source_lang: str,
        target_lang: str,
        glossary_prompt: str = ""
    ) -> Tuple[str, int]:
        """Traduce un fragmento de artículo preservando formato técnico y aplicando glosario."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada. Ingrésala en la barra lateral o archivo .env")

        prompt = f"""Eres un traductor científico y académico experto de nivel Senior.
Tu tarea es traducir con la máxima precisión, naturalidad y fidelidad el siguiente fragmento de un artículo del idioma '{source_lang}' al '{target_lang}'.

REGLAS ESENCIALES DE TRADUCCIÓN:
1. Emplea un registro formal, claro y adecuado para publicaciones académicas y científicas indexadas.
2. No agregues saludos, explicaciones ni notas introductorias; devuelve EXCLUSIVAMENTE el texto traducido.
{glossary_prompt}

REGLAS CRÍTICAS DE FORMATO (violar cualquiera de estas es INACEPTABLE):
1. Preserva EXACTAMENTE toda la jerarquía de encabezados Markdown: # (H1), ## (H2), ### (H3), #### (H4). NO cambies el nivel ni elimines encabezados.
2. Preserva EXACTAMENTE negritas (**texto**) y cursivas (*texto*) donde aparezcan.
3. Preserva EXACTAMENTE las tablas Markdown con su estructura | columna | columna |, traduciendo solo el contenido de las celdas.
4. Preserva EXACTAMENTE la numeración de secciones (1., 2.1., 3.1.2.) sin alterarla.
5. Preserva EXACTAMENTE fórmulas LaTeX ($...$, $$...$$) y bloques de código (```...```) sin traducirlos.
6. Preserva EXACTAMENTE listas con viñetas (- item) y listas numeradas (1. item).
7. Preserva EXACTAMENTE los comentarios de página (<!-- [PAGE X] -->) sin modificarlos.
8. Preserva EXACTAMENTE las referencias bibliográficas [1], [2, 3], (Smith et al., 2020) sin traducirlas.

TEXTO ORIGINAL A TRADUCIR:
\"\"\"
{chunk_text}
\"\"\"

TRADUCCIÓN AL {target_lang.upper()}:"""

        translated_text = GeminiClient.generate_text(
            prompt=prompt,
            api_key=self.api_key,
            preferred_model=self.model_name,
            temperature=self.temperature
        )

        tokens = (len(prompt) + len(translated_text)) // 4
        return translated_text, tokens
