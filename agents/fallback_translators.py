import requests
from typing import Tuple
from config import Config

class FallbackTranslator:
    """Manejo de traducción directa (API Web externa o Gemini directo)."""

    @staticmethod
    def translate_via_web_api(text: str, source_lang: str, target_lang: str, api_url: str = None, api_key: str = None) -> Tuple[str, int]:
        """Envía solicitud a una API de traducción HTTP compatible."""
        url = api_url or Config.WEB_TRANSLATOR_URL
        key = api_key or Config.WEB_TRANSLATOR_KEY

        if not url:
            raise ValueError("URL del traductor web no configurada.")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Adaptar según formato de respuesta común
        translated = data.get("translatedText") or data.get("translation") or data.get("result", "")
        tokens = len(text) // 4
        return translated, tokens
