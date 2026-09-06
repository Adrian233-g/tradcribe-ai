import io
import os
import zipfile
from typing import List, Tuple
from database.connection import get_db
from database.models import Lote, Documento
from parsers.docx_parser import DocxParser
from parsers.pdf_generator import PDFGenerator

class ExportService:
    @staticmethod
    def get_document_export(doc_id: int, format_type: str = "pdf") -> Tuple[str, bytes]:
        """Genera el archivo para descarga individual de un documento traducido (PDF, DOCX, MD, TXT)."""
        with get_db() as db:
            doc = db.query(Documento).filter(Documento.id == doc_id).first()
            if not doc:
                raise ValueError("Documento no encontrado.")

            base_name, _ = os.path.splitext(doc.nombre_archivo)
            content = doc.contenido_traducido or ""

            if format_type.lower() == "pdf":
                filename = f"[ES]_{base_name}.pdf"
                file_bytes = PDFGenerator.create_pdf_from_markdown(content, document_title=base_name)
                return filename, file_bytes
            elif format_type.lower() == "docx":
                filename = f"[ES]_{base_name}.docx"
                file_bytes = DocxParser.create_docx_from_markdown(content)
                return filename, file_bytes
            elif format_type.lower() == "md":
                filename = f"[ES]_{base_name}.md"
                file_bytes = content.encode("utf-8")
                return filename, file_bytes
            else: # txt
                filename = f"[ES]_{base_name}.txt"
                file_bytes = content.encode("utf-8")
                return filename, file_bytes

    @staticmethod
    def export_batch_zip(lote_id: int, format_type: str = "pdf") -> Tuple[str, bytes]:
        """Genera un archivo .ZIP conteniendo todas las traducciones del lote en el formato solicitado."""
        with get_db() as db:
            lote = db.query(Lote).filter(Lote.id == lote_id).first()
            if not lote:
                raise ValueError("Lote no encontrado.")

            docs = db.query(Documento).filter(Documento.lote_id == lote_id).all()

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for doc in docs:
                    if not doc.contenido_traducido:
                        continue
                    base_name, _ = os.path.splitext(doc.nombre_archivo)
                    content = doc.contenido_traducido

                    if format_type.lower() == "pdf":
                        file_bytes = PDFGenerator.create_pdf_from_markdown(content, document_title=base_name)
                        zip_file.writestr(f"[ES]_{base_name}.pdf", file_bytes)
                    elif format_type.lower() == "docx":
                        file_bytes = DocxParser.create_docx_from_markdown(content)
                        zip_file.writestr(f"[ES]_{base_name}.docx", file_bytes)
                    elif format_type.lower() == "md":
                        zip_file.writestr(f"[ES]_{base_name}.md", content.encode("utf-8"))
                    else:
                        zip_file.writestr(f"[ES]_{base_name}.txt", content.encode("utf-8"))

            zip_buffer.seek(0)
            zip_name = f"Traducciones_Lote_{lote.id}_{lote.nombre.replace(' ', '_')}_{format_type.upper()}.zip"
            return zip_name, zip_buffer.getvalue()
