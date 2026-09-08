import logging
import time
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)

class GeminiClient:
    """Cliente unificado y ultra-resiliente para Google Gemini API con auto-descubrimiento dinámico de modelos."""

    _models_cache: dict = {}
    _working_model_cache: dict = {}
    _session = requests.Session()

    @classmethod
    def get_available_models(cls, api_key: str) -> List[str]:
        """Consulta directamente a Google qué modelos están habilitados para la clave (con caché)."""
        clean_k = api_key.strip().strip('"').strip("'")
        if clean_k in cls._models_cache and cls._models_cache[clean_k]:
            return cls._models_cache[clean_k]

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_k}"
        try:
            r = cls._session.get(url, timeout=10)
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
        preferred_model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_retries: int = 3
    ) -> str:
        if not api_key or not api_key.strip():
            raise ValueError("GEMINI_API_KEY no suministrada. Configúrala en la barra lateral o archivo .env.")

        api_key = api_key.strip().strip('"').strip("'")
        clean_model = preferred_model.replace("models/", "").strip() if preferred_model else "gemini-2.5-flash"

        # 1. Obtener modelos descubiertos para esta API key
        discovered = cls.get_available_models(api_key)

        # 2. Priorizar el modelo preferido, luego el último exitoso, luego los descubiertos
        candidates = []
        if clean_model:
            candidates.append(clean_model)
        
        last_working = cls._working_model_cache.get(api_key)
        if last_working and last_working not in candidates:
            candidates.append(last_working)

        for m in discovered:
            if m not in candidates:
                candidates.append(m)

        fallback_standards = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro"
        ]
        for m in fallback_standards:
            if m not in candidates:
                candidates.append(m)

        errors = []

        for attempt in range(max_retries):
            for model_name in candidates:
                for api_ver in ["v1beta", "v1"]:
                    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={api_key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": temperature}
                    }
                    try:
                        response = cls._session.post(url, json=payload, headers=headers, timeout=60)

                        if response.status_code == 200:
                            data = response.json()
                            candidates_list = data.get("candidates", [])
                            if candidates_list:
                                parts = candidates_list[0].get("content", {}).get("parts", [])
                                if parts:
                                    cls._working_model_cache[api_key] = model_name
                                    return parts[0].get("text", "").strip()

                        elif response.status_code == 429:
                            sleep_time = 1.5 * (attempt + 1)
                            time.sleep(sleep_time)
                            errors.append(f"Rate Limit (429) en {model_name}")
                            break
                        elif response.status_code in [404, 400]:
                            continue
                        else:
                            errors.append(f"{model_name} (HTTP {response.status_code}): {response.text[:80]}")
                    except Exception as e:
                        errors.append(f"{model_name}: {str(e)}")

            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))

        last_error_summary = "\n".join(errors[-2:]) if errors else "Error desconocido de comunicación con Google API"
        raise RuntimeError(f"Error en Gemini API:\n{last_error_summary}")
