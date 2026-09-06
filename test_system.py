import os
import sys
from database.connection import get_db, DB_STATUS, DB_TYPE
from database.models import Lote, Documento, Glosario, FragmentoDocumento, RegistroAgente
from database.migrations import initialize_database
from parsers.text_parser import TextParser
from parsers.docx_parser import DocxParser
from agents.parser_agent import DocumentChunker
from agents.glossary_agent import GlossaryAgent
from services.export_service import ExportService

def run_tests():
    print("=== 1. TEST DE BASE DE DATOS POSTGRESQL ===")
    initialize_database()
    print(f"Estado de BD: {DB_STATUS} ({DB_TYPE})")

    with get_db() as db:
        glosario_count = db.query(Glosario).count()
        print(f"✓ Total de términos en glosario: {glosario_count}")
        assert glosario_count >= 9, "El glosario debería tener al menos 9 términos."

    print("\n=== 2. TEST DE DETECCIÓN DE GLOSARIO EN TEXTO ===")
    sample_text = "Modern Machine Learning frameworks achieve state-of-the-art results on this benchmark."
    matches = GlossaryAgent.find_glossary_terms(sample_text, "en", "es")
    print(f"✓ Términos detectados en texto de muestra: {matches}")
    assert len(matches) >= 2, f"Se esperaban al menos 2 términos detectados, encontrados: {len(matches)}"

    prompt_glossary = GlossaryAgent.format_glossary_prompt(matches)
    print("✓ Prompt de glosario generado correctamente.")

    print("\n=== 3. TEST DE SEGMENTACIÓN INTELIGENTE (CHUNKING) ===")
    with open("samples/article_1_ai_advances.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    chunks = DocumentChunker.chunk_text(md_text, max_chunk_size=500)
    print(f"✓ Documento dividido en {len(chunks)} fragmentos.")
    assert len(chunks) >= 1, "Debe haber al menos 1 chunk."

    print("\n=== 4. TEST DE PARSERS Y EXPORTADOR DOCX/ZIP ===")
    docx_bytes = DocxParser.create_docx_from_markdown(md_text)
    print(f"✓ DOCX generado con éxito ({len(docx_bytes)} bytes).")
    assert len(docx_bytes) > 0, "El DOCX generado no debe estar vacío."

    # Test de inserción y exportación de lote simulado
    with get_db() as db:
        test_lote = Lote(
            nombre="Lote_Test_Automatizado",
            idioma_origen="en",
            idioma_destino="es",
            modo_pipeline="multi_agente",
            estado="completado",
            total_documentos=1,
            documentos_completados=1
        )
        db.add(test_lote)
        db.flush()

        test_doc = Documento(
            lote_id=test_lote.id,
            nombre_archivo="articulo_test.md",
            contenido_original=md_text,
            contenido_traducido="# Avances Recientes en Aprendizaje Profundo y Modelos de Lenguaje Extensos\n\nEste es un texto traducido de prueba.",
            estado="completado",
            total_palabras=25,
            puntuacion_calidad=4.9
        )
        db.add(test_doc)
        db.flush()

        # Probar generación de ZIP
        zip_name, zip_bytes = ExportService.export_batch_zip(test_lote.id, "docx")
        print(f"✓ Archivo ZIP generado: '{zip_name}' ({len(zip_bytes)} bytes).")
        assert len(zip_bytes) > 0, "El archivo ZIP no debe estar vacío."

    print("\n=== 5. TEST DE AGENTE DEEPL Y GEMINI OPTIMIZADO ===")
    from agents.deepl_translator import DeepLTranslatorAgent
    from agents.gemini_client import GeminiClient

    assert "en" in DeepLTranslatorAgent.LANG_MAP_SOURCE
    assert "es" in DeepLTranslatorAgent.LANG_MAP_TARGET
    print("✓ Mapeo de idiomas de DeepL verificado.")

    # Validar que get_usage maneja clave vacía con elegancia
    usage_res = DeepLTranslatorAgent.get_usage("")
    assert usage_res["valid"] is False
    print("✓ Manejo de estado/errores de DeepL validado.")

    # Validar que la caché de GeminiClient está presente
    assert hasattr(GeminiClient, "_models_cache")
    assert hasattr(GeminiClient, "_working_model_cache")
    print("\n=== 6. TEST DE GENERADOR DE PDF PROFESIONAL (0 TOKENS) ===")
    from parsers.pdf_generator import PDFGenerator
    sample_academic_md = """# Transformer Architecture Advances in 2026

## 1. Introducción y Metodología
Los modelos autorregresivos han demostrado capacidades sin precedentes en procesamiento de lenguaje natural [1].

### Características Principales:
- **Atención Multicabezal:** Mejora la representación semántica contextual.
- *Inferencia Optimizada:* Reduce la latencia computacional en un 40%.
- `FlashAttention-3`: Implementación nativa de kernels acelerados.

| Parámetro | Valor Previo | Valor Optimizado |
| --- | --- | --- |
| Latencia (ms) | 120ms | 45ms |
| Precisión Top-1 | 88.4% | 93.1% |

> "La preservación del formato estructural es esencial para la reproducibilidad de la investigación científica."

```python
def benchmark():
    return {"status": "success", "tokens_spent": 0}
```
"""
    pdf_bytes = PDFGenerator.create_pdf_from_markdown(sample_academic_md, "Artículo de Prueba")
    print(f"✓ PDF Académico generado exitosamente ({len(pdf_bytes)} bytes) con 0 consumo de tokens.")
    assert len(pdf_bytes) > 1000, "El PDF generado debe tener contenido válido."

    # Probar exportación de PDF individual y en ZIP
    with get_db() as db:
        test_doc_pdf = db.query(Documento).first()
        if test_doc_pdf:
            fn, b = ExportService.get_document_export(test_doc_pdf.id, "pdf")
            assert fn.endswith(".pdf") and len(b) > 0
            print(f"✓ Exportación individual PDF validada: '{fn}'")

            zip_fn, zip_b = ExportService.export_batch_zip(test_doc_pdf.lote_id, "pdf")
            assert zip_fn.endswith(".zip") and len(zip_b) > 0
            print(f"✓ Exportación masiva ZIP (PDFs) validada: '{zip_fn}'")

    print("\n==========================================")
    print("🎉 ¡TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
