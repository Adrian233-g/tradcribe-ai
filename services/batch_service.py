import os
import time
from typing import List, Dict, Any, Optional, Callable
from database.connection import get_db
from database.models import Lote, Documento
from parsers.pdf_parser import PDFParser
from parsers.docx_parser import DocxParser
from parsers.text_parser import TextParser
from agents.agent_pipeline import TranslationPipeline

class BatchService:
    @staticmethod
    def create_batch(
        nombre: str,
        idioma_origen: str,
        idioma_destino: str,
        modo_pipeline: str,
        uploaded_files: List[Any]
    ) -> int:
        """Registra un nuevo lote y extrae el texto de todos los archivos cargados."""
        with get_db() as db:
            lote = Lote(
                nombre=nombre,
                idioma_origen=idioma_origen,
                idioma_destino=idioma_destino,
                modo_pipeline=modo_pipeline,
                estado="pendiente",
                total_documentos=len(uploaded_files),
                documentos_completados=0
            )
            db.add(lote)
            db.flush() # Obtener lote.id

            lote_id = lote.id

            for uploaded_file in uploaded_files:
                filename = uploaded_file.name
                file_bytes = uploaded_file.getvalue()
                mime_type = uploaded_file.type or "text/plain"
                ext = os.path.splitext(filename)[1].lower()

                # Crear registro preliminar para obtener doc.id
                doc = Documento(
                    lote_id=lote_id,
                    nombre_archivo=filename,
                    tipo_mime=mime_type,
                    tamano_bytes=len(file_bytes),
                    contenido_original="",
                    estado="pendiente",
                    total_palabras=0
                )
                db.add(doc)
                db.flush()

                # Extraer texto según extensión vinculando doc.id para imágenes
                if ext == ".pdf":
                    text_content = PDFParser.extract_text(file_bytes, doc_id=doc.id)
                elif ext in [".docx", ".doc"]:
                    text_content = DocxParser.extract_text(file_bytes)
                else: # .txt, .md, etc.
                    text_content = TextParser.extract_text(file_bytes)

                doc.contenido_original = text_content
                doc.total_palabras = len(text_content.split())

            return lote_id

    @staticmethod
    def process_batch(
        lote_id: int,
        gemini_api_key: Optional[str] = None,
        deepl_api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ):
        """Ejecuta la traducción de todos los documentos de un lote."""
        start_time = time.time()

        with get_db() as db:
            lote = db.query(Lote).filter(Lote.id == lote_id).first()
            if not lote:
                raise ValueError(f"Lote {lote_id} no encontrado.")

            lote.estado = "en_proceso"
            idioma_origen = lote.idioma_origen
            idioma_destino = lote.idioma_destino
            modo = lote.modo_pipeline

            docs = db.query(Documento).filter(Documento.lote_id == lote_id).all()
            total_docs = len(docs)
            doc_data_list = [(d.id, d.nombre_archivo, d.contenido_original) for d in docs]

        pipeline = TranslationPipeline(
            gemini_api_key=gemini_api_key,
            deepl_api_key=deepl_api_key,
            model_name=model_name,
            critic_enabled=True,
            mode=modo,
            log_callback=log_callback
        )

        completed_count = 0

        for idx, (doc_id, filename, raw_content) in enumerate(doc_data_list):
            if cancel_check and cancel_check():
                break

            if progress_callback:
                progress_callback(idx + 1, total_docs, f"Traduciendo artículo {idx+1}/{total_docs}: '{filename}'")

            with get_db() as db:
                doc = db.query(Documento).filter(Documento.id == doc_id).first()
                if doc:
                    doc.estado = "traduciendo"

            # Procesar documento con el pipeline de agentes
            doc_state = pipeline.process_document(
                document_id=doc_id,
                filename=filename,
                raw_text=raw_content or "",
                source_lang=idioma_origen,
                target_lang=idioma_destino,
                lote_id=lote_id,
                cancel_check=cancel_check
            )

            if doc_state.status == "cancelado" or (cancel_check and cancel_check()):
                break

            completed_count += 1
            with get_db() as db:
                lote_ref = db.query(Lote).filter(Lote.id == lote_id).first()
                if lote_ref:
                    lote_ref.documentos_completados = completed_count

        total_time = time.time() - start_time
        with get_db() as db:
            lote_final = db.query(Lote).filter(Lote.id == lote_id).first()
            if lote_final:
                if cancel_check and cancel_check():
                    lote_final.estado = "cancelado"
                else:
                    lote_final.estado = "completado"
                lote_final.tiempo_segundos = round(total_time, 2)
