import io
import re
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
from pypdf import PdfReader

# pdfminer.six para extracción granular de fuentes y posiciones
from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LAParams, LTTextContainer, LTChar, LTAnno,
    LTTextLine, LTTextBox, LTFigure, LTPage
)


class StructuredLine:
    """Representa una línea de texto con metadatos tipográficos."""
    __slots__ = ('text', 'font_size', 'font_name', 'is_bold', 'is_italic', 'x0', 'y0', 'page_num')

    def __init__(self, text: str, font_size: float, font_name: str,
                 is_bold: bool, is_italic: bool, x0: float, y0: float, page_num: int):
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.is_bold = is_bold
        self.is_italic = is_italic
        self.x0 = x0
        self.y0 = y0
        self.page_num = page_num


class PDFParser:
    """Extractor inteligente de estructura desde PDFs usando análisis de fuentes."""

    # Umbrales de indentación para detectar listas (en puntos tipográficos)
    _INDENT_THRESHOLD = 36  # ~0.5 pulgadas

    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        """Extrae texto estructurado con reconocimiento de encabezados, negritas, cursivas y tablas."""
        try:
            structured_lines = PDFParser._extract_with_pdfminer(file_bytes)
            if structured_lines:
                return PDFParser._reconstruct_markdown(structured_lines)
        except Exception:
            pass

        # Fallback: extracción básica con pypdf
        return PDFParser._fallback_extract(file_bytes)

    @staticmethod
    def _extract_with_pdfminer(file_bytes: bytes) -> List[StructuredLine]:
        """Extrae líneas con metadatos de fuente usando pdfminer.six."""
        laparams = LAParams(
            line_margin=0.3,
            word_margin=0.15,
            char_margin=2.0,
            boxes_flow=0.5
        )

        structured_lines: List[StructuredLine] = []
        file_stream = io.BytesIO(file_bytes)

        for page_num, page_layout in enumerate(extract_pages(file_stream, laparams=laparams), start=1):
            for element in page_layout:
                if isinstance(element, (LTTextBox, LTTextContainer)):
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            line_info = PDFParser._analyze_line(text_line, page_num)
                            if line_info and line_info.text.strip():
                                structured_lines.append(line_info)
                elif isinstance(element, LTTextLine):
                    line_info = PDFParser._analyze_line(element, page_num)
                    if line_info and line_info.text.strip():
                        structured_lines.append(line_info)

        return structured_lines

    @staticmethod
    def _analyze_line(text_line: LTTextLine, page_num: int) -> Optional[StructuredLine]:
        """Analiza una línea de texto extrayendo fuente, tamaño, negrita y cursiva."""
        chars_info: List[Dict] = []

        for char in text_line:
            if isinstance(char, LTChar):
                chars_info.append({
                    'char': char.get_text(),
                    'font_name': char.fontname or '',
                    'font_size': round(char.size, 1),
                })
            elif isinstance(char, LTAnno):
                chars_info.append({
                    'char': char.get_text(),
                    'font_name': '',
                    'font_size': 0,
                })

        if not chars_info:
            return None

        # Obtener la fuente dominante (la más frecuente, ignorando espacios y annotations)
        real_chars = [c for c in chars_info if c['font_size'] > 0]
        if not real_chars:
            text = ''.join(c['char'] for c in chars_info)
            return StructuredLine(text, 0, '', False, False, text_line.x0, text_line.y0, page_num)

        # Fuente dominante por frecuencia
        font_counter: Dict[str, int] = defaultdict(int)
        size_counter: Dict[float, int] = defaultdict(int)

        for c in real_chars:
            font_counter[c['font_name']] += 1
            size_counter[c['font_size']] += 1

        dominant_font = max(font_counter, key=font_counter.get)
        dominant_size = max(size_counter, key=size_counter.get)

        # Detectar negrita e itálica por nombre de fuente
        font_lower = dominant_font.lower()
        is_bold = any(tag in font_lower for tag in ['bold', 'black', 'heavy', 'demi', 'semibold'])
        is_italic = any(tag in font_lower for tag in ['italic', 'oblique', 'inclined', 'slanted'])

        text = ''.join(c['char'] for c in chars_info).strip()

        return StructuredLine(
            text=text,
            font_size=dominant_size,
            font_name=dominant_font,
            is_bold=is_bold,
            is_italic=is_italic,
            x0=text_line.x0,
            y0=text_line.y0,
            page_num=page_num
        )

    @staticmethod
    def _reconstruct_markdown(lines: List[StructuredLine]) -> str:
        """Reconstruye markdown estructurado a partir de las líneas analizadas."""
        if not lines:
            return ""

        # Calcular estadísticas de tamaño de fuente para determinar body text
        size_freq: Dict[float, int] = defaultdict(int)
        for line in lines:
            if line.font_size > 0:
                size_freq[line.font_size] += len(line.text)

        if not size_freq:
            return "\n".join(l.text for l in lines)

        # El tamaño de body text es el que acumula más caracteres
        body_size = max(size_freq, key=size_freq.get)

        # Determinar umbrales de heading relativos al body
        h1_threshold = body_size + 4.0   # Títulos principales: ≥ body + 4pt
        h2_threshold = body_size + 2.0   # Subsecciones: ≥ body + 2pt
        h3_threshold = body_size + 0.5   # Sub-subsecciones: ≥ body + 0.5pt

        markdown_parts: List[str] = []
        current_page = 0
        current_paragraph_lines: List[str] = []

        def flush_paragraph():
            if current_paragraph_lines:
                merged = " ".join(current_paragraph_lines)
                # Limpiar guiones de fin de línea del PDF
                merged = re.sub(r'(\w)- (\w)', r'\1\2', merged)
                markdown_parts.append(merged)
                current_paragraph_lines.clear()

        for line in lines:
            text = line.text.strip()
            if not text:
                continue

            # Marcador de página
            if line.page_num != current_page:
                flush_paragraph()
                current_page = line.page_num
                markdown_parts.append(f"\n<!-- [PAGE {current_page}] -->")

            # Detectar si es un heading
            is_heading = False

            if line.font_size >= h1_threshold and line.is_bold:
                flush_paragraph()
                markdown_parts.append(f"\n# {text}")
                is_heading = True
            elif line.font_size >= h2_threshold and (line.is_bold or line.font_size > body_size + 2.5):
                flush_paragraph()
                markdown_parts.append(f"\n## {text}")
                is_heading = True
            elif line.font_size >= h3_threshold and line.is_bold:
                flush_paragraph()
                markdown_parts.append(f"\n### {text}")
                is_heading = True
            # Headings por patrón textual (secciones numeradas como "1. Introduction", "2.1 Methods")
            elif re.match(r'^\d+(\.\d+)*\.?\s+[A-ZÁÉÍÓÚÑ]', text) and line.is_bold:
                flush_paragraph()
                # Detectar nivel por profundidad de numeración
                num_match = re.match(r'^(\d+(?:\.\d+)*)', text)
                depth = num_match.group(1).count('.') + 1 if num_match else 1
                prefix = '#' * min(depth + 1, 4)  # ## para nivel 1, ### para nivel 2
                markdown_parts.append(f"\n{prefix} {text}")
                is_heading = True
            # Detectar "Abstract", "Introduction", "Conclusion", "References" como headings comunes
            elif line.is_bold and text.lower() in [
                'abstract', 'introduction', 'conclusion', 'conclusions',
                'references', 'bibliography', 'acknowledgements', 'acknowledgments',
                'methods', 'methodology', 'results', 'discussion',
                'materials and methods', 'supplementary material',
                'resumen', 'introducción', 'conclusión', 'conclusiones',
                'referencias', 'bibliografía', 'agradecimientos',
                'métodos', 'metodología', 'resultados', 'discusión'
            ]:
                flush_paragraph()
                markdown_parts.append(f"\n## {text}")
                is_heading = True

            if not is_heading:
                # Aplicar formato inline
                formatted = text

                # Línea completamente en negrita (y no es heading) → aplicar **bold**
                if line.is_bold and len(text) < 200:
                    formatted = f"**{text}**"
                elif line.is_italic:
                    formatted = f"*{text}*"

                # Detectar listas por indentación o marcadores
                if re.match(r'^[•●○◦▪▸►–—]\s*', text):
                    flush_paragraph()
                    clean = re.sub(r'^[•●○◦▪▸►–—]\s*', '', text)
                    markdown_parts.append(f"- {clean}")
                elif re.match(r'^\d+[.)]\s+', text) and len(text) < 300:
                    flush_paragraph()
                    markdown_parts.append(formatted)
                else:
                    # Acumular como parte del párrafo actual
                    # Si hay un salto de Y grande, flush
                    current_paragraph_lines.append(formatted)

        flush_paragraph()

        result = "\n\n".join(part for part in markdown_parts if part.strip())

        # Limpieza final
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    @staticmethod
    def _fallback_extract(file_bytes: bytes) -> str:
        """Fallback con pypdf cuando pdfminer falla."""
        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned = PDFParser._clean_page_text(page_text)
            extracted_pages.append(f"<!-- [PAGE {i+1}] -->\n{cleaned}")
        return "\n\n".join(extracted_pages)

    @staticmethod
    def _clean_page_text(text: str) -> str:
        """Limpieza básica de texto extraído con pypdf."""
        lines = [line.strip() for line in text.split("\n")]
        paragraphs = []
        current_p = []

        for line in lines:
            if not line:
                if current_p:
                    paragraphs.append(" ".join(current_p))
                    current_p = []
            elif line.endswith(("-", "—")):
                current_p.append(line[:-1])
            else:
                current_p.append(line)

        if current_p:
            paragraphs.append(" ".join(current_p))

        return "\n\n".join(paragraphs)
