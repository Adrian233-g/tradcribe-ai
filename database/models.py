import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Lote(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    idioma_origen = Column(String(10), default="en", nullable=False)
    idioma_destino = Column(String(10), default="es", nullable=False)
    modo_pipeline = Column(String(50), default="multi_agente", nullable=False) # 'multi_agente', 'gemini_directo', 'web_api'
    estado = Column(String(50), default="pendiente", nullable=False) # 'pendiente', 'en_proceso', 'completado', 'error', 'cancelado'
    total_documentos = Column(Integer, default=0)
    documentos_completados = Column(Integer, default=0)
    tiempo_segundos = Column(Float, default=0.0)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    documentos = relationship("Documento", back_populates="lote", cascade="all, delete-orphan")
    registros = relationship("RegistroAgente", back_populates="lote", cascade="all, delete-orphan")

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lote_id = Column(Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    tipo_mime = Column(String(100), default="text/plain")
    tamano_bytes = Column(Integer, default=0)
    contenido_original = Column(Text, nullable=True)
    contenido_traducido = Column(Text, nullable=True)
    estado = Column(String(50), default="pendiente") # 'pendiente', 'traduciendo', 'revisando', 'completado', 'error'
    total_palabras = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    puntuacion_calidad = Column(Float, nullable=True) # 1.0 - 5.0 o 0 - 100
    mensaje_error = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    lote = relationship("Lote", back_populates="documentos")
    fragmentos = relationship("FragmentoDocumento", back_populates="documento", cascade="all, delete-orphan")
    registros = relationship("RegistroAgente", back_populates="documento", cascade="all, delete-orphan")

class FragmentoDocumento(Base):
    __tablename__ = "fragmentos_documento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    indice = Column(Integer, nullable=False)
    contenido_original = Column(Text, nullable=False)
    contenido_traducido = Column(Text, nullable=True)
    notas_critico = Column(Text, nullable=True)
    estado = Column(String(50), default="pendiente") # 'pendiente', 'traducido', 'revisado', 'error'
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    documento = relationship("Documento", back_populates="fragmentos")

class Glosario(Base):
    __tablename__ = "glosario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    termino_origen = Column(String(255), nullable=False)
    termino_destino = Column(String(255), nullable=False)
    idioma_origen = Column(String(10), default="en", nullable=False)
    idioma_destino = Column(String(10), default="es", nullable=False)
    dominio = Column(String(100), default="General") # 'Medicina', 'Ingeniería', 'IA', 'General', etc.
    notas = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

class RegistroAgente(Base):
    __tablename__ = "registros_agente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lote_id = Column(Integer, ForeignKey("lotes.id", ondelete="CASCADE"), nullable=True)
    documento_id = Column(Integer, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=True)
    agente = Column(String(100), nullable=False) # 'Extractor', 'Glosario', 'Traductor', 'Critico', 'Reensamblador'
    nivel = Column(String(20), default="INFO") # 'INFO', 'WARNING', 'ERROR', 'SUCCESS'
    mensaje = Column(Text, nullable=False)
    detalles_json = Column(JSON, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    lote = relationship("Lote", back_populates="registros")
    documento = relationship("Documento", back_populates="registros")
