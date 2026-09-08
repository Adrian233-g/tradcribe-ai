import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv(override=True)

class Config:
    # Base de Datos PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "tradcribe_db")

    @classmethod
    def get_db_url(cls) -> str:
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"

    @classmethod
    def get_default_postgres_url(cls) -> str:
        """URL para conectar a la BD por defecto 'postgres' y crear 'tradcribe_db' si no existe."""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/postgres"

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # DeepL API
    DEEPL_API_KEY: str = os.getenv("DEEPL_API_KEY", "")

    # Web Translator API externa (opcional)
    WEB_TRANSLATOR_URL: str = os.getenv("WEB_TRANSLATOR_URL", "")
    WEB_TRANSLATOR_KEY: str = os.getenv("WEB_TRANSLATOR_KEY", "")

    # Configuración de Agentes - Optimizado para alta velocidad con Gemini 2.0 Flash
    AGENT_MAX_CHUNK_SIZE: int = int(os.getenv("AGENT_MAX_CHUNK_SIZE", "14000"))
    AGENT_CRITIC_ENABLED: bool = os.getenv("AGENT_CRITIC_ENABLED", "true").lower() == "true"
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.2"))
    AGENT_MAX_CONCURRENCY: int = int(os.getenv("AGENT_MAX_CONCURRENCY", "5"))

    # Idiomas soportados
    SUPPORTED_LANGUAGES = {
        "en": "Inglés",
        "es": "Español",
        "fr": "Francés",
        "de": "Alemán",
        "pt": "Portugués",
        "it": "Italiano",
        "zh": "Chino (Mandarín)",
        "ja": "Japonés",
        "ru": "Ruso",
        "ar": "Árabe"
    }
