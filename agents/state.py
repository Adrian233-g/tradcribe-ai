from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChunkState(BaseModel):
    chunk_index: int
    original_text: str
    glossary_matches: Dict[str, str] = Field(default_factory=dict)
    draft_translation: Optional[str] = None
    critic_feedback: Optional[str] = None
    final_translation: Optional[str] = None
    quality_score: Optional[float] = None
    tokens_used: int = 0
    logs: List[Dict[str, Any]] = Field(default_factory=list)

class DocumentTranslationState(BaseModel):
    document_id: Optional[int] = None
    filename: str
    source_language: str
    target_language: str
    raw_content: str
    chunks: List[ChunkState] = Field(default_factory=list)
    assembled_translation: Optional[str] = None
    total_tokens: int = 0
    average_quality_score: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None
