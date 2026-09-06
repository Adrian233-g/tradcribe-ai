import re
from typing import List

class DocumentChunker:
    """Divide artículos científicos y técnicos en fragmentos coherentes respetando párrafos y estructura."""

    @staticmethod
    def chunk_text(text: str, max_chunk_size: int = 2500) -> List[str]:
        if not text or not text.strip():
            return []

        # Normalizar saltos de línea
        text = text.replace("\r\n", "\n")

        # Separar por párrafos
        paragraphs = re.split(r'\n{2,}', text)
        chunks = []
        current_chunk = []
        current_length = 0

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            p_len = len(p_clean)

            # Si el párrafo por sí solo supera el tamaño máximo, dividirlo por oraciones
            if p_len > max_chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                sentences = re.split(r'(?<=[.!?])\s+', p_clean)
                sub_chunk = []
                sub_length = 0
                for s in sentences:
                    s_len = len(s)
                    if sub_length + s_len > max_chunk_size and sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = [s]
                        sub_length = s_len
                    else:
                        sub_chunk.append(s)
                        sub_length += s_len + 1
                if sub_chunk:
                    chunks.append(" ".join(sub_chunk))
                continue

            if current_length + p_len > max_chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [p_clean]
                current_length = p_len
            else:
                current_chunk.append(p_clean)
                current_length += p_len + 2 # Considerando \n\n

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks
