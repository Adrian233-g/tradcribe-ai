import logging
from database.connection import create_tables, get_db, DB_STATUS, DB_TYPE
from database.models import Glosario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GLOSARIO_INICIAL = [
    {"termino_origen": "Machine Learning", "termino_destino": "Aprendizaje Automático", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Inteligencia Artificial", "notas": "Término estándar en publicaciones científicas."},
    {"termino_origen": "Deep Learning", "termino_destino": "Aprendizaje Profundo", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Inteligencia Artificial", "notas": ""},
    {"termino_origen": "Large Language Model", "termino_destino": "Modelo de Lenguaje Extenso (LLM)", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Inteligencia Artificial", "notas": ""},
    {"termino_origen": "State-of-the-Art", "termino_destino": "Estado del Arte / Estado de la Técnica", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Académico", "notas": ""},
    {"termino_origen": "Framework", "termino_destino": "Marco de Trabajo (Framework)", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Ingeniería de Software", "notas": ""},
    {"termino_origen": "Benchmark", "termino_destino": "Punto de Referencia / Evaluación Comparativa", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Académico", "notas": ""},
    {"termino_origen": "Pipeline", "termino_destino": "Flujo de Procesamiento (Pipeline)", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Ingeniería", "notas": ""},
    {"termino_origen": "Trade-off", "termino_destino": "Compromiso / Balance", "idioma_origen": "en", "idioma_destino": "es", "dominio": "General", "notas": ""},
    {"termino_origen": "Peer-reviewed", "termino_destino": "Revisado por Pares", "idioma_origen": "en", "idioma_destino": "es", "dominio": "Académico", "notas": ""}
]

def initialize_database():
    """Crea las tablas e inserta los datos iniciales de glosario si la tabla está vacía."""
    logger.info(f"Estado de BD: {DB_STATUS} (Tipo: {DB_TYPE})")
    logger.info("Creando tablas en la base de datos...")
    create_tables()
    logger.info("Tablas creadas exitosamente.")

    with get_db() as db:
        count = db.query(Glosario).count()
        if count == 0:
            logger.info("Poblando glosario inicial de términos técnicos y científicos...")
            for item in GLOSARIO_INICIAL:
                glosario_item = Glosario(**item)
                db.add(glosario_item)
            logger.info(f"Se insertaron {len(GLOSARIO_INICIAL)} términos iniciales en el glosario.")
        else:
            logger.info(f"El glosario ya contiene {count} términos registrados.")

if __name__ == "__main__":
    initialize_database()
