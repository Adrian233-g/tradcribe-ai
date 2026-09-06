import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config
from database.models import Base

logger = logging.getLogger(__name__)

# Intentar inicializar la base de datos PostgreSQL
def init_postgres_db():
    """Verifica si la base de datos 'tradcribe_db' existe en PostgreSQL, si no, la crea."""
    try:
        # Conectar a la base de datos por defecto 'postgres'
        admin_engine = create_engine(
            Config.get_default_postgres_url(),
            isolation_level="AUTOCOMMIT"
        )
        with admin_engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname='{Config.DB_NAME}'")
            )
            exists = result.scalar() is not None
            if not exists:
                logger.info(f"Creando base de datos '{Config.DB_NAME}' en PostgreSQL...")
                conn.execute(text(f"CREATE DATABASE {Config.DB_NAME}"))
                logger.info(f"Base de datos '{Config.DB_NAME}' creada con éxito.")
        admin_engine.dispose()
    except Exception as e:
        logger.warning(f"No se pudo verificar/crear la BD PostgreSQL automáticamente: {e}")

# Crear engine para la aplicación
try:
    init_postgres_db()
    db_url = Config.get_db_url()
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    # Probar conexión
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    DB_STATUS = "PostgreSQL Conectado"
    DB_TYPE = "postgresql"
except Exception as e:
    logger.error(f"Error conectando a PostgreSQL ({e}). Usando SQLite como respaldo local...")
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tradcribe_local.db")
    db_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    DB_STATUS = f"SQLite Local (PostgreSQL desconectado: {e})"
    DB_TYPE = "sqlite"

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine))

def get_engine():
    return engine

@contextmanager
def get_db():
    """Generador de sesiones de base de datos seguro."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_tables():
    """Crea todas las tablas definidas en los modelos."""
    Base.metadata.create_all(bind=engine)
