import logging
import requests
from typing import Tuple, Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class DeepLTranslatorAgent:
    """Agente de Traducción Ultra-rápido utilizando la API oficial de DeepL (Free o Pro)."""

    LANG_MAP_SOURCE = {
        "en": "EN",
        "es": "ES",
        "fr": "FR",
        "de": "DE",
        "pt": "PT",
        "it": "IT",
        "zh": "ZH",
        "ja": "JA",
        "ru": "RU",
        "ar": "AR"
    }

    LANG_MAP_TARGET = {
        "en": "EN-US",
        "es": "ES",
        "fr": "FR",
        "de": "DE",
        "pt": "PT-BR",
        "it": "IT",
        "zh": "ZH-HANS",
        "ja": "JA",
        "ru": "RU",
        "ar": "AR"
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or Config.DEEPL_API_KEY or "").strip().strip('"').strip("'")

    @classmethod
    def get_base_url(cls, api_key: str) -> str:
        """Determina la URL base según si la clave es del plan Free (:fx) o Pro."""
        key = api_key.strip()
        if key.endswith(":fx"):
            return "https://api-free.deepl.com/v2"
        return "https://api.deepl.com/v2"

    @classmethod
    def get_usage(cls, api_key: str) -> Dict[str, Any]:
        """Consulta el consumo mensual de caracteres y el límite de la cuenta DeepL."""
        if not api_key:
            return {"valid": False, "error": "API Key no suministrada."}

        clean_key = api_key.strip().strip('"').strip("'")
        base_url = cls.get_base_url(clean_key)
        url = f"{base_url}/usage"

        headers = {
            "Authorization": f"DeepL-Auth-Key {clean_key}",
            "User-Agent": "TradcribeAI/1.0"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = data.get("character_count", 0)
                limit = data.get("character_limit", 500000)
                pct = (count / limit * 100) if limit else 0.0
                plan_type = "Free (500k/mes)" if clean_key.endswith(":fx") else "Pro (Ilimitado/Pago)"
                return {
                    "valid": True,
                    "character_count": count,
                    "character_limit": limit,
                    "percent_used": round(pct, 1),
                    "plan_type": plan_type
                }
            elif response.status_code == 403:
                return {"valid": False, "error": "Clave API de DeepL inválida o no autorizada (HTTP 403)."}
            else:
                return {"valid": False, "error": f"Error DeepL ({response.status_code}): {response.text}"}
        except Exception as e:
            return {"valid": False, "error": f"Error de conexión con DeepL: {str(e)}"}

    def translate_chunk(
        self,
        chunk_text: str,
        source_lang: str,
        target_lang: str
    ) -> Tuple[str, int]:
        """Traduce un fragmento de texto de forma ultrarrápida manteniendo formato."""
        if not self.api_key:
            raise ValueError("DEEPL_API_KEY no configurada. Ingrésala en la barra lateral o archivo .env")

        base_url = self.get_base_url(self.api_key)
        url = f"{base_url}/translate"

        s_lang = self.LANG_MAP_SOURCE.get(source_lang.lower(), source_lang.upper())
        t_lang = self.LANG_MAP_TARGET.get(target_lang.lower(), target_lang.upper())

        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TradcribeAI/1.0"
        }

        payload = {
            "text": [chunk_text],
            "target_lang": t_lang,
            "preserve_formatting": True
        }

        if s_lang and s_lang != "AUTO":
            payload["source_lang"] = s_lang

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            translations = data.get("translations", [])
            if translations:
                translated_text = translations[0].get("text", "")
                tokens = len(chunk_text) // 4
                return translated_text, tokens
            raise RuntimeError("Respuesta de DeepL sin traducciones.")
        elif response.status_code == 403:
            raise PermissionError("DeepL API Key inválida o cuota superada (HTTP 403).")
        elif response.status_code == 456:
            raise RuntimeError("Cuota mensual de DeepL excedida (HTTP 456).")
        else:
            raise RuntimeError(f"Error DeepL ({response.status_code}): {response.text}")
