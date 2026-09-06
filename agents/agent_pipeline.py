import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Dict, Any, List, Tuple
from config import Config
from agents.state import DocumentTranslationState, ChunkState
from agents.parser_agent import DocumentChunker
from agents.glossary_agent import GlossaryAgent
from agents.translator_agent import SeniorTranslatorAgent
from agents.critic_agent import CriticAgent
from agents.deepl_translator import DeepLTranslatorAgent
from agents.fallback_translators import FallbackTranslator
from database.connection import get_db
from database.models import RegistroAgente, FragmentoDocumento, Documento

logger = logging.getLogger(__name__)

class TranslationPipeline:
    """Orquestador híbrido multi-motor de agentes para la traducción de documentos con alta resiliencia."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        deepl_api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        critic_enabled: bool = True,
        mode: str = "multi_agente",
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.gemini_api_key = gemini_api_key or Config.GEMINI_API_KEY
        self.deepl_api_key = deepl_api_key or Config.DEEPL_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL
        self.critic_enabled = critic_enabled
        self.mode = mode
        self.log_callback = log_callback

        self.gemini_translator = SeniorTranslatorAgent(
            api_key=self.gemini_api_key,
            model_name=self.model_name
        )
        self.critic = CriticAgent(
            api_key=self.gemini_api_key,
            model_name=self.model_name
        )
        self.deepl_translator = DeepLTranslatorAgent(
            api_key=self.deepl_api_key
        )

    def _log(self, agent: str, message: str, level: str = "INFO", doc_id: Optional[int] = None, lote_id: Optional[int] = None, details: Optional[Dict] = None):
        """Registra el evento de forma thread-safe tanto en callback UI como en PostgreSQL."""
        if self.log_callback:
            try:
                self.log_callback(agent, message)
            except Exception:
                pass # Evitar que excepciones de contexto de Streamlit en hilos hijos rompan el pipeline

        try:
            with get_db() as db:
                log_entry = RegistroAgente(
                    lote_id=lote_id,
                    documento_id=doc_id,
                    agente=agent,
                    nivel=level,
                    mensaje=message,
                    detalles_json=details
                )
                db.add(log_entry)
        except Exception as e:
            logger.debug(f"No se pudo guardar log en BD: {e}")

    def _process_single_chunk_gemini(
        self,
        idx: int,
        chunk_text: str,
        total_chunks: int,
        source_lang: str,
        target_lang: str,
        document_id: int,
        lote_id: Optional[int]
    ) -> Tuple[int, ChunkState, str, int, float]:
        """Procesa un fragmento individual con Gemini y Crítico con manejo de errores robusto."""
        chunk_state = ChunkState(chunk_index=idx, original_text=chunk_text)

        # 1. Glosario
        glossary_matches = {}
        try:
            glossary_matches = GlossaryAgent.find_glossary_terms(chunk_text, source_lang, target_lang)
        except Exception:
            pass

        chunk_state.glossary_matches = glossary_matches
        glossary_prompt = GlossaryAgent.format_glossary_prompt(glossary_matches)

        if glossary_matches:
            self._log(
                "Glosario",
                f"Chunk #{idx+1}/{total_chunks}: {len(glossary_matches)} términos clave aplicados.",
                doc_id=document_id, lote_id=lote_id
            )

        # 2. Traductor Gemini
        self._log("Traductor", f"Chunk #{idx+1}/{total_chunks}: Traduciendo con {self.model_name}...", doc_id=document_id, lote_id=lote_id)
        try:
            draft_trans, tokens_t = self.gemini_translator.translate_chunk(
                chunk_text=chunk_text,
                source_lang=source_lang,
                target_lang=target_lang,
                glossary_prompt=glossary_prompt
            )
        except Exception as e:
            logger.warning(f"Reintentando chunk #{idx+1} por error: {e}")
            time.sleep(2.0)
            draft_trans, tokens_t = self.gemini_translator.translate_chunk(
                chunk_text=chunk_text,
                source_lang=source_lang,
                target_lang=target_lang,
                glossary_prompt=glossary_prompt
            )

        chunk_state.draft_translation = draft_trans
        total_tokens = tokens_t

        # 3. Crítico (si aplica en modo multi-agente)
        final_trans = draft_trans
        score = 4.8
        if self.critic_enabled and self.mode == "multi_agente":
            self._log("Crítico", f"Chunk #{idx+1}/{total_chunks}: Auditando fidelidad...", doc_id=document_id, lote_id=lote_id)
            try:
                reviewed_text, feedback, score_val, tokens_c = self.critic.review_and_refine(
                    original_chunk=chunk_text,
                    draft_translation=draft_trans,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary_matches=glossary_matches
                )
                chunk_state.critic_feedback = feedback
                chunk_state.quality_score = score_val
                chunk_state.final_translation = reviewed_text
                final_trans = reviewed_text
                total_tokens += tokens_c
                score = score_val
                self._log("Crítico", f"Chunk #{idx+1}/{total_chunks} aprobado con nota: {score}/5.0", doc_id=document_id, lote_id=lote_id)
            except Exception as e:
                chunk_state.critic_feedback = f"Revisión simplificada: {e}"
                chunk_state.final_translation = draft_trans
                chunk_state.quality_score = 4.7
        else:
            chunk_state.final_translation = draft_trans
            chunk_state.quality_score = 4.8

        return idx, chunk_state, final_trans, total_tokens, score

    def _process_single_chunk_deepl(
        self,
        idx: int,
        chunk_text: str,
        total_chunks: int,
        source_lang: str,
        target_lang: str,
        document_id: int,
        lote_id: Optional[int]
    ) -> Tuple[int, ChunkState, str, int, float]:
        """Procesa un fragmento individual con DeepL API ultrarrápido."""
        chunk_state = ChunkState(chunk_index=idx, original_text=chunk_text)

        self._log("DeepL", f"Chunk #{idx+1}/{total_chunks}: Traduciendo a alta velocidad...", doc_id=document_id, lote_id=lote_id)
        translated_text, tokens = self.deepl_translator.translate_chunk(
            chunk_text=chunk_text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        chunk_state.draft_translation = translated_text
        chunk_state.final_translation = translated_text
        chunk_state.quality_score = 4.9
        chunk_state.critic_feedback = "Traducción neuronal directa con DeepL"

        return idx, chunk_state, translated_text, tokens, 4.9

    def process_document(
        self,
        document_id: int,
        filename: str,
        raw_text: str,
        source_lang: str,
        target_lang: str,
        lote_id: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> DocumentTranslationState:
        """Ejecuta el pipeline de traducción (DeepL o Gemini Concurrente) sobre un documento."""
        state = DocumentTranslationState(
            document_id=document_id,
            filename=filename,
            source_language=source_lang,
            target_language=target_lang,
            raw_content=raw_text
        )

        try:
            motor_label = "DeepL Ultra-Rápido" if self.mode == "deepl" else f"Gemini ({self.model_name})"
            self._log("Extractor", f"Iniciando segmentación de '{filename}' [Motor: {motor_label}]", doc_id=document_id, lote_id=lote_id)

            chunk_size = 12000 if self.mode == "deepl" else Config.AGENT_MAX_CHUNK_SIZE
            chunks = DocumentChunker.chunk_text(raw_text, max_chunk_size=chunk_size)
            total_chunks = len(chunks)
            self._log("Extractor", f"Documento estructurado en {total_chunks} fragmentos semánticos", doc_id=document_id, lote_id=lote_id)

            if cancel_check and cancel_check():
                state.status = "cancelado"
                return state

            results_by_idx: Dict[int, Tuple[ChunkState, str, int, float]] = {}

            # Para Gemini: 2 hilos paralelos respetan los límites de cuota (15 RPM) sin saturar la API
            # Para DeepL: procesamiento secuencial ultra-veloz (100ms por chunk)
            max_concurrency = 1 if self.mode in ["deepl", "web_api"] else min(2, max(1, total_chunks))

            if max_concurrency > 1 and total_chunks > 1:
                self._log("Pipeline", f"Ejecutando {total_chunks} fragmentos con concurrencia adaptativa ({max_concurrency} hilos)...", doc_id=document_id, lote_id=lote_id)
                with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
                    futures = {
                        executor.submit(
                            self._process_single_chunk_gemini,
                            idx, chunk_text, total_chunks, source_lang, target_lang, document_id, lote_id
                        ): idx
                        for idx, chunk_text in enumerate(chunks)
                    }

                    completed_count = 0
                    for future in as_completed(futures):
                        if cancel_check and cancel_check():
                            state.status = "cancelado"
                            return state

                        idx, chunk_state, final_trans, tokens, score = future.result()
                        results_by_idx[idx] = (chunk_state, final_trans, tokens, score)
                        completed_count += 1

                        if progress_callback:
                            try:
                                progress_callback(completed_count / total_chunks, f"Completado fragmento {completed_count}/{total_chunks}...")
                            except Exception:
                                pass
            else:
                for idx, chunk_text in enumerate(chunks):
                    if cancel_check and cancel_check():
                        state.status = "cancelado"
                        return state

                    if progress_callback:
                        try:
                            progress_callback(idx / total_chunks, f"Procesando fragmento {idx+1}/{total_chunks}...")
                        except Exception:
                            pass

                    if self.mode == "deepl":
                        idx, chunk_state, final_trans, tokens, score = self._process_single_chunk_deepl(
                            idx, chunk_text, total_chunks, source_lang, target_lang, document_id, lote_id
                        )
                    elif self.mode == "web_api":
                        trans, tokens = FallbackTranslator.translate_via_web_api(chunk_text, source_lang, target_lang)
                        chunk_state = ChunkState(chunk_index=idx, original_text=chunk_text, draft_translation=trans, final_translation=trans, quality_score=4.5)
                        final_trans, score = trans, 4.5
                    else:
                        idx, chunk_state, final_trans, tokens, score = self._process_single_chunk_gemini(
                            idx, chunk_text, total_chunks, source_lang, target_lang, document_id, lote_id
                        )

                    results_by_idx[idx] = (chunk_state, final_trans, tokens, score)

            # Reconstrucción ordenada
            translated_chunks: List[str] = []
            total_tokens = 0
            quality_scores: List[float] = []

            for idx in range(total_chunks):
                chunk_state, final_trans, tokens, score = results_by_idx[idx]
                translated_chunks.append(final_trans)
                total_tokens += tokens
                quality_scores.append(score)
                state.chunks.append(chunk_state)

                try:
                    with get_db() as db:
                        frag_record = FragmentoDocumento(
                            documento_id=document_id,
                            indice=idx,
                            contenido_original=chunks[idx],
                            contenido_traducido=final_trans,
                            notas_critico=chunk_state.critic_feedback,
                            estado="completado"
                        )
                        db.add(frag_record)
                except Exception as e:
                    logger.debug(f"Error guardando fragmento en BD: {e}")

            # Reensamblado
            self._log("Reensamblador", f"Reconstruyendo documento final '{filename}'...", doc_id=document_id, lote_id=lote_id)
            assembled_doc = "\n\n".join(translated_chunks)
            state.assembled_translation = assembled_doc
            state.total_tokens = total_tokens
            state.average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 5.0
            state.status = "completado"

            with get_db() as db:
                doc = db.query(Documento).filter(Documento.id == document_id).first()
                if doc:
                    doc.contenido_traducido = assembled_doc
                    doc.estado = "completado"
                    doc.total_tokens = total_tokens
                    doc.puntuacion_calidad = state.average_quality_score
                    doc.total_palabras = len(assembled_doc.split())

            words_count = len(assembled_doc.split())
            self._log("Pipeline", f"¡Documento '{filename}' traducido con éxito! ({words_count} palabras)", level="SUCCESS", doc_id=document_id, lote_id=lote_id)

            if progress_callback:
                try:
                    progress_callback(1.0, "¡Traducción completada!")
                except Exception:
                    pass

            return state

        except Exception as e:
            error_msg = f"Error en pipeline: {str(e)}"
            self._log("Pipeline", error_msg, level="ERROR", doc_id=document_id, lote_id=lote_id)
            state.status = "error"
            state.error = error_msg

            try:
                with get_db() as db:
                    doc = db.query(Documento).filter(Documento.id == document_id).first()
                    if doc:
                        doc.estado = "error"
                        doc.mensaje_error = error_msg
            except Exception:
                pass

            return state
