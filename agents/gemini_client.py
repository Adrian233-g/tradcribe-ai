import logging
import time
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)

class GeminiClient:
    """Cliente unificado y ultra-resiliente para Google Gemini API con auto-descubrimiento, reintentos y backoff."""

    _models_cache: dict = {}
    _working_model_cache: dict = {}

    @classmethod
    def get_available_models(cls, api_key: str) -> List[str]:
        """Consulta directamente a Google qué modelos están habilitados para la clave (con caché)."""
        clean_k = api_key.strip().strip('"').strip("'")
        if clean_k in cls._models_cache and cls._models_cache[clean_k]:
            return cls._models_cache[clean_k]

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_k}"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                models = [
                    m['name'].replace("models/", "")
                    for m in data.get('models', [])
                    if 'generateContent' in m.get('supportedGenerationMethods', [])
                ]
                if models:
                    cls._models_cache[clean_k] = models
                    return models
        except Exception as e:
            logger.debug(f"No se pudieron auto-descubrir modelos: {e}")
        return []

    @classmethod
    def generate_text(
        cls,
        prompt: str,
        api_key: str,
        preferred_model: str = "gemini-2.0-flash",
        temperature: float = 0.2,
        max_retries: int = 3
    ) -> str:
        if not api_key or not api_key.strip():
            raise ValueError("GEMINI_API_KEY no suministrada. Configúrala en la barra lateral o archivo .env.")

        api_key = api_key.strip().strip('"').strip("'")
        clean_model = preferred_model.replace("models/", "").strip()

        # 1. Obtener modelos descubiertos o lista estándar de alta compatibilidad
        discovered = cls.get_available_models(api_key)

        default_candidates = [
            clean_model,
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-2.5-flash"
        ]

        # Priorizar último modelo que haya respondido con éxito
        last_working = cls._working_model_cache.get(api_key)
        if last_working and last_working in default_candidates:
            ordered_candidates = [last_working] + [m for m in default_candidates if m != last_working]
        else:
            ordered_candidates = default_candidates

        model_list = ([clean_model] if clean_model else []) + (discovered if discovered else []) + ordered_candidates
        seen = set()
        candidates = [m for m in model_list if not (m in seen or seen.add(m))]

        errors = []

        # Intentar llamada con reintentos para manejar límites 429 de Google Free Tier
        for attempt in range(max_retries):
            for model_name in candidates:
                for api_ver in ["v1beta", "v1"]:
                    try:
                        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={api_key}"
                        headers = {"Content-Type": "application/json"}
                        payload = {
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": temperature}
                        }
                        response = requests.post(url, json=payload, headers=headers, timeout=60)

                        if response.status_code == 200:
                            data = response.json()
                            candidates_list = data.get("candidates", [])
                            if candidates_list:
                                parts = candidates_list[0].get("content", {}).get("parts", [])
                                if parts:
                                    cls._working_model_cache[api_key] = model_name
                                    return parts[0].get("text", "").strip()

                        elif response.status_code == 429:
                            # Cuota/Rate Limit: Esperar con backoff exponencial
                            sleep_time = 2.0 * (attempt + 1)
                            time.sleep(sleep_time)
                            errors.append(f"Rate Limit (HTTP 429) en {model_name}, reintentando en {sleep_time}s...")
                            break # Pasar al siguiente intento
                        elif response.status_code == 404:
                            # Modelo no existe en esta versión, probar siguiente
                            continue
                        else:
                            errors.append(f"{api_ver}/{model_name} (HTTP {response.status_code}): {response.text[:100]}")
                    except Exception as e:
                        errors.append(f"{api_ver}/{model_name}: {str(e)}")

            # Pequeña pausa entre rondas de reintento si hubo errores
            if attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))

        last_error_summary = "\n".join(errors[-3:]) if errors else "Error desconocido de comunicación con Google API"
        raise RuntimeError(f"Error en Gemini API:\n{last_error_summary}")
