import csv
import io
from typing import List, Dict, Optional, Any
from database.connection import get_db
from database.models import Glosario

class GlossaryService:
    @staticmethod
    def get_all(dominio: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene la lista de términos como diccionarios puros dentro de la sesión de BD."""
        with get_db() as db:
            query = db.query(Glosario)
            if dominio and dominio != "Todos":
                query = query.filter(Glosario.dominio == dominio)
            if search:
                term = f"%{search.lower()}%"
                query = query.filter(
                    (Glosario.termino_origen.ilike(term)) |
                    (Glosario.termino_destino.ilike(term)) |
                    (Glosario.notas.ilike(term))
                )
            results = query.order_by(Glosario.termino_origen.asc()).all()
            return [
                {
                    "id": t.id,
                    "termino_origen": str(t.termino_origen),
                    "termino_destino": str(t.termino_destino),
                    "idioma_origen": str(t.idioma_origen),
                    "idioma_destino": str(t.idioma_destino),
                    "dominio": str(t.dominio),
                    "notas": str(t.notas or "")
                }
                for t in results
            ]

    @staticmethod
    def add_term(termino_origen: str, termino_destino: str, idioma_origen: str = "en", idioma_destino: str = "es", dominio: str = "General", notas: str = ""):
        """Agrega un nuevo término al glosario de PostgreSQL."""
        with get_db() as db:
            item = Glosario(
                termino_origen=termino_origen.strip(),
                termino_destino=termino_destino.strip(),
                idioma_origen=idioma_origen,
                idioma_destino=idioma_destino,
                dominio=dominio,
                notas=notas
            )
            db.add(item)
            db.flush()
            return item.id

    @staticmethod
    def delete_term(term_id: int):
        """Elimina un término del glosario."""
        with get_db() as db:
            term = db.query(Glosario).filter(Glosario.id == term_id).first()
            if term:
                db.delete(term)

    @staticmethod
    def import_csv(csv_content: str) -> int:
        """Importa términos masivamente desde un archivo CSV."""
        reader = csv.DictReader(io.StringIO(csv_content))
        count = 0
        with get_db() as db:
            for row in reader:
                orig = row.get("termino_origen") or row.get("source") or row.get("origen")
                dest = row.get("termino_destino") or row.get("target") or row.get("destino")
                if not orig or not dest:
                    continue
                dominio = row.get("dominio") or row.get("domain") or "General"
                notas = row.get("notas") or row.get("notes") or ""
                item = Glosario(
                    termino_origen=orig.strip(),
                    termino_destino=dest.strip(),
                    idioma_origen="en",
                    idioma_destino="es",
                    dominio=dominio,
                    notas=notas
                )
                db.add(item)
                count += 1
        return count
