import os
import io
import re
import time
from typing import List, Tuple, Dict, Optional, Any
from collections import defaultdict
from PIL import Image
import pdfplumber
from pypdf import PdfReader


class StructuredElement:
    """Elemento estructurado con posición vertical para ordenamiento topológico."""
    __slots__ = ('elem_type', 'top', 'content', 'extra')

    def __init__(self, elem_type: str, top: float, content: str, extra: Optional[Dict] = None):
        self.elem_type = elem_type  # 'heading1', 'heading2', 'heading3', 'paragraph', 'table', 'image', 'equation', 'list'
        self.top = top
        self.content = content
        self.extra = extra or {}


class PDFParser:
    """
    Extractor de estructura de alta fidelidad desde PDFs.
    Soporta:
    - Fusión inteligente de encabezados y títulos multilínea.
    - Extracción estructurada de tablas a Markdown nativo.
    - Extracción y persistencia de imágenes con marcadores markdown.
    - Detección y preservación de ecuaciones matemáticas.
    """

    MEDIA_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "extracted_images")

    @classmethod
    def extract_text(cls, file_bytes: bytes, doc_id: Optional[Any] = None) -> str:
        """Extrae texto estructurado completo con tablas, imágenes, fórmulas y encabezados fusionados."""
        if not file_bytes:
            return ""

        try:
            markdown = cls._extract_with_pdfplumber(file_bytes, doc_id=doc_id)
            if markdown and len(markdown.strip()) > 30:
                return markdown
        except Exception as e:
            # Fallback a pdfminer/pypdf si pdfplumber falla
            pass

        return cls._fallback_extract(file_bytes)

    @classmethod
    def _extract_with_pdfplumber(cls, file_bytes: bytes, doc_id: Optional[Any] = None) -> str:
        """Extrae páginas de forma estructurada usando pdfplumber con detección de tablas, imágenes y texto ordenado."""
        doc_folder_name = f"doc_{doc_id}" if doc_id else f"temp_{int(time.time()*1000)}"
        media_doc_dir = os.path.join(cls.MEDIA_BASE_DIR, doc_folder_name)
        os.makedirs(media_doc_dir, exist_ok=True)

        pages_markdown: List[str] = []
        fig_counter = 1

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return ""

            # Paso 1: Análisis global de frecuencias de fuentes para determinar body_size
            font_sizes: Dict[float, int] = defaultdict(int)
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=['size', 'fontname', 'non_stroking_color'])
                for w in words:
                    sz = round(float(w.get('size', 10.0)), 1)
                    if sz > 0:
                        font_sizes[sz] += len(w.get('text', ''))

            body_size = max(font_sizes, key=font_sizes.get) if font_sizes else 10.0
            h1_threshold = body_size + 3.0
            h2_threshold = body_size + 1.5
            h3_threshold = body_size + 0.4

            for page_num, page in enumerate(pdf.pages, start=1):
                page_elements: List[StructuredElement] = []
                table_bboxes = []

                # ── 1. Extracción de Tablas Reales (solo líneas y bordes explícitos) ──
                tables = page.find_tables()

                for t in tables:
                    try:
                        table_data = t.extract()
                        if table_data and len(table_data) >= 2 and 2 <= len(table_data[0]) <= 15:
                            md_table = cls._table_to_markdown(table_data)
                            if md_table:
                                bbox = t.bbox  # (x0, top, x1, bottom)
                                table_bboxes.append(bbox)
                                page_elements.append(StructuredElement(
                                    elem_type='table',
                                    top=bbox[1],
                                    content=md_table
                                ))
                    except Exception:
                        pass

                # ── 2. Extracción de Imágenes ──
                try:
                    if hasattr(page, 'images') and page.images:
                        for img_idx, img_info in enumerate(page.images):
                            w = float(img_info.get('width', 0))
                            h = float(img_info.get('height', 0))
                            # Filtrar artefactos minúsculos (iconos decorativos, líneas de separación < 25px)
                            if w < 25 or h < 25:
                                continue

                            # Intentar extraer los bytes de imagen
                            img_obj = img_info.get('stream')
                            img_filename = f"fig_p{page_num}_{img_idx+1}.png"
                            img_filepath = os.path.join(media_doc_dir, img_filename)
                            rel_img_path = f"media/extracted_images/{doc_folder_name}/{img_filename}"

                            saved = False
                            if img_obj:
                                try:
                                    raw_data = img_obj.get_data()
                                    if raw_data:
                                        pil_img = Image.open(io.BytesIO(raw_data))
                                        pil_img.save(img_filepath, format="PNG")
                                        saved = True
                                except Exception:
                                    pass

                            # Si no se pudo obtener del stream directo, recortar la región de la página
                            if not saved:
                                try:
                                    bbox = (
                                        max(0, float(img_info.get('x0', 0))),
                                        max(0, float(img_info.get('top', 0))),
                                        min(page.width, float(img_info.get('x1', page.width))),
                                        min(page.height, float(img_info.get('bottom', page.height)))
                                    )
                                    if bbox[2] > bbox[0] + 10 and bbox[3] > bbox[1] + 10:
                                        cropped = page.crop(bbox)
                                        page_img = cropped.to_image(resolution=150)
                                        page_img.save(img_filepath, format="PNG")
                                        saved = True
                                except Exception:
                                    pass

                            if saved:
                                img_tag = f"![Figura {fig_counter}: Imagen extraída de la página {page_num}]({rel_img_path})"
                                fig_counter += 1
                                page_elements.append(StructuredElement(
                                    elem_type='image',
                                    top=float(img_info.get('top', 0)),
                                    content=img_tag
                                ))
                except Exception:
                    pass

                # ── 3. Extracción de Líneas de Texto (excluyendo zonas de tablas) ──
                # Extraer palabras con atributos
                words = page.extract_words(
                    extra_attrs=['size', 'fontname', 'non_stroking_color'],
                    keep_blank_chars=False
                )

                # Filtrar palabras que caen dentro de las tablas detectadas
                valid_words = []
                for w in words:
                    w_x0 = float(w.get('x0', 0))
                    w_top = float(w.get('top', 0))
                    w_x1 = float(w.get('x1', 0))
                    w_bottom = float(w.get('bottom', 0))

                    in_table = False
                    for (tx0, ttop, tx1, tbottom) in table_bboxes:
                        if not (w_x1 < tx0 or w_x0 > tx1 or w_bottom < ttop or w_top > tbottom):
                            in_table = True
                            break

                    if not in_table:
                        valid_words.append(w)

                # Agrupar palabras en líneas de texto por proximidad vertical
                text_lines = cls._group_words_into_lines(valid_words)

                # Clasificar y agrupar líneas (Smart Heading Fusion & Equation Detection)
                structured_text_elements = cls._process_page_text_lines(
                    text_lines=text_lines,
                    body_size=body_size,
                    h1_threshold=h1_threshold,
                    h2_threshold=h2_threshold,
                    h3_threshold=h3_threshold,
                    is_first_page=(page_num == 1)
                )

                page_elements.extend(structured_text_elements)

                # ── 4. Ordenamiento Topológico Vertical ──
                # Ordenar todos los elementos de la página por su posición Y superior (top)
                page_elements.sort(key=lambda el: el.top)

                # Renderizar Markdown de la página
                page_md_parts = [f"<!-- [PAGE {page_num}] -->"]
                for el in page_elements:
                    if el.content and el.content.strip():
                        page_md_parts.append(el.content.strip())

                pages_markdown.append("\n\n".join(page_md_parts))

        full_markdown = "\n\n".join(pages_markdown)
        # Limpieza de saltos excesivos
        full_markdown = re.sub(r'\n{3,}', '\n\n', full_markdown)
        return full_markdown.strip()

    @staticmethod
    def _group_words_into_lines(words: List[Dict]) -> List[Dict]:
        """Agrupa palabras en líneas visuales basadas en su coordenada vertical 'top'."""
        if not words:
            return []

        # Ordenar palabras primero por top y luego por x0
        sorted_words = sorted(words, key=lambda w: (round(float(w.get('top', 0)) / 3.0), float(w.get('x0', 0))))

        lines: List[Dict] = []
        current_line_words: List[Dict] = []
        current_top = None

        for w in sorted_words:
            w_top = float(w.get('top', 0))
            w_size = float(w.get('size', 10.0))
            vertical_tolerance = max(2.5, w_size * 0.35)

            if current_top is None:
                current_top = w_top
                current_line_words.append(w)
            elif abs(w_top - current_top) <= vertical_tolerance:
                current_line_words.append(w)
            else:
                # Flush línea anterior
                if current_line_words:
                    lines.append(PDFParser._build_line_dict(current_line_words))
                current_line_words = [w]
                current_top = w_top

        if current_line_words:
            lines.append(PDFParser._build_line_dict(current_line_words))

        # Ordenar líneas estrictamente por su 'top'
        lines.sort(key=lambda l: l['top'])
        return lines

    @staticmethod
    def _build_line_dict(words: List[Dict]) -> Dict:
        """Construye un diccionario de línea a partir de sus palabras con fuente dominante."""
        # Ordenar palabras horizontalmente
        words_sorted = sorted(words, key=lambda w: float(w.get('x0', 0)))
        text_parts = []
        for i, w in enumerate(words_sorted):
            text_parts.append(w.get('text', ''))

        line_text = " ".join(text_parts).strip()
        # Limpiar espacios antes de signos de puntuación
        line_text = re.sub(r'\s+([,.:;?!%])', r'\1', line_text)

        font_sizes = [float(w.get('size', 10)) for w in words_sorted if w.get('size')]
        avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 10.0

        font_names = [str(w.get('fontname', '')).lower() for w in words_sorted]
        is_bold = any(any(tag in fn for tag in ['bold', 'black', 'heavy', 'demi', 'semibold', 'b']) for fn in font_names)
        is_italic = any(any(tag in fn for tag in ['italic', 'oblique', 'inclined', 'slanted', 'i']) for fn in font_names)

        top_val = min(float(w.get('top', 0)) for w in words_sorted)
        bottom_val = max(float(w.get('bottom', top_val + avg_size)) for w in words_sorted)
        x0_val = min(float(w.get('x0', 0)) for w in words_sorted)

        return {
            'text': line_text,
            'size': avg_size,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'top': top_val,
            'bottom': bottom_val,
            'x0': x0_val
        }

    @classmethod
    def _process_page_text_lines(
        cls,
        text_lines: List[Dict],
        body_size: float,
        h1_threshold: float,
        h2_threshold: float,
        h3_threshold: float,
        is_first_page: bool
    ) -> List[StructuredElement]:
        """Procesa líneas de texto realizando Fusión de Títulos Multilínea y detección de fórmulas."""
        elements: List[StructuredElement] = []
        n = len(text_lines)
        i = 0

        # Heurística para secciones científicas estándar
        section_names = {
            'abstract', 'introduction', 'conclusion', 'conclusions',
            'references', 'bibliography', 'acknowledgements', 'acknowledgments',
            'methods', 'methodology', 'results', 'discussion', 'results and discussion',
            'materials and methods', 'supplementary material', 'background', 'related work',
            'resumen', 'introducción', 'conclusión', 'conclusiones',
            'referencias', 'bibliografía', 'agradecimientos',
            'métodos', 'metodología', 'resultados', 'discusión', 'materiales y métodos'
        }

        while i < n:
            line = text_lines[i]
            text = line['text'].strip()
            if not text:
                i += 1
                continue

            size = line['size']
            is_bold = line['is_bold']
            top_pos = line['top']

            # ── A. Título Principal Multilínea (Página 1 o tamaño >= h1_threshold) ──
            if (is_first_page and i == 0 and (size >= h1_threshold or is_bold)) or (size >= h1_threshold and is_bold):
                title_lines = [text]
                j = i + 1
                while j < n:
                    next_line = text_lines[j]
                    next_text = next_line['text'].strip()
                    next_size = next_line['size']
                    next_bold = next_line['is_bold']
                    vert_gap = next_line['top'] - line['bottom']

                    # Fusión si la línea siguiente tiene estilo similar de título y está próxima verticalmente
                    if (abs(next_size - size) <= 2.0 or next_bold) and next_size >= (body_size + 1.5) and vert_gap < (size * 2.2):
                        # Limpiar guión de corte de palabra
                        if title_lines[-1].endswith(("-", "—")):
                            title_lines[-1] = title_lines[-1][:-1] + next_text
                        else:
                            title_lines.append(next_text)
                        line = next_line  # actualizar límites
                        j += 1
                    else:
                        break

                full_title = " ".join(title_lines)
                full_title = re.sub(r'\s{2,}', ' ', full_title)
                elements.append(StructuredElement('heading1', top_pos, f"# {full_title}"))
                i = j
                continue

            # ── B. Subencabezados H2 Multilínea o Secciones Numeradas ──
            is_numbered_sec = bool(re.match(r'^\d+(\.\d+)*\.?\s+[A-ZÁÉÍÓÚÑ]', text))
            is_common_sec = (text.lower() in section_names or text.lower().rstrip(':') in section_names)

            if (size >= h2_threshold and (is_bold or size > body_size + 2.0)) or (is_numbered_sec and is_bold) or (is_common_sec and is_bold):
                h2_lines = [text]
                j = i + 1
                while j < n:
                    next_line = text_lines[j]
                    next_text = next_line['text'].strip()
                    next_size = next_line['size']
                    next_bold = next_line['is_bold']
                    vert_gap = next_line['top'] - line['bottom']

                    # Si el subencabezado ocupaba dos líneas
                    if next_bold and abs(next_size - size) <= 1.5 and vert_gap < (size * 1.8) and not re.match(r'^\d+(\.\d+)*\.', next_text):
                        if h2_lines[-1].endswith(("-", "—")):
                            h2_lines[-1] = h2_lines[-1][:-1] + next_text
                        else:
                            h2_lines.append(next_text)
                        line = next_line
                        j += 1
                    else:
                        break

                full_h2 = " ".join(h2_lines)
                elements.append(StructuredElement('heading2', top_pos, f"## {full_h2}"))
                i = j
                continue

            # ── C. Sub-subencabezados H3 ──
            if size >= h3_threshold and is_bold and len(text) < 150:
                elements.append(StructuredElement('heading3', top_pos, f"### {text}"))
                i += 1
                continue

            # ── D. Fórmulas Matemáticas y Ecuaciones ──
            if cls._is_equation_line(text):
                eq_content = text
                # Envolver en bloque LaTeX para máxima protección durante la traducción
                if not eq_content.startswith("$$"):
                    eq_content = f"$$\n{eq_content}\n$$"
                elements.append(StructuredElement('equation', top_pos, eq_content))
                i += 1
                continue

            # ── E. Listas con viñeta o numeradas ──
            if re.match(r'^[•●○◦▪▸►–—]\s*', text):
                clean_item = re.sub(r'^[•●○◦▪▸►–—]\s*', '', text)
                elements.append(StructuredElement('list', top_pos, f"- {clean_item}"))
                i += 1
                continue
            elif re.match(r'^\d+[.)]\s+', text) and len(text) < 250:
                elements.append(StructuredElement('list', top_pos, text))
                i += 1
                continue

            # ── F. Párrafos de Texto Regular (con acumulación continua) ──
            para_lines = [text]
            j = i + 1
            while j < n:
                next_line = text_lines[j]
                next_text = next_line['text'].strip()
                if not next_text:
                    j += 1
                    break

                next_size = next_line['size']
                next_bold = next_line['is_bold']
                vert_gap = next_line['top'] - line['bottom']

                # Detener acumulación de párrafo si la siguiente línea es un heading, tabla, ecuación o lista
                if (next_size >= h2_threshold and next_bold) or cls._is_equation_line(next_text) or re.match(r'^[•●○◦▪▸►–—]\s*', next_text) or (next_size >= h1_threshold):
                    break

                # Si hay un salto vertical grande, es separación de párrafo
                line_height = max(10.0, size)
                if vert_gap > (line_height * 1.8):
                    break

                # Unir con tratamiento de guiones al final de línea
                if para_lines[-1].endswith(("-", "—")):
                    para_lines[-1] = para_lines[-1][:-1] + next_text
                else:
                    para_lines.append(next_text)

                line = next_line
                j += 1

            full_para = " ".join(para_lines)
            full_para = re.sub(r'\s{2,}', ' ', full_para)
            elements.append(StructuredElement('paragraph', top_pos, full_para))
            i = j

        return elements

    @staticmethod
    def _is_equation_line(text: str) -> bool:
        """Determina si una línea contiene una fórmula matemática o ecuación aislada."""
        s = text.strip()
        if not s or len(s) > 300:
            return False

        # Patrones de ecuación explícita numerada: e.g. "P = a * b + c (1)" o "Eq. 1:"
        has_eq_num = bool(re.search(r'\(\d+[a-zA-Z]?\)\s*$', s) or re.match(r'^(?:Eq\.|Equation|Ecuación)\s*\d+', s, re.I))

        # Símbolos matemáticos característicos
        math_symbols = ['=', '≈', '≠', '≤', '≥', '∑', '∫', '∏', '√', '∂', 'α', 'β', 'γ', 'δ', 'ε', 'θ', 'λ', 'μ', 'σ', 'π', '±', '×', '÷', '∈']
        symbol_count = sum(1 for sym in math_symbols if sym in s)

        # Expresiones algebraicas típicas con subíndices o variables
        has_algebra = bool(re.search(r'[a-zA-Z]_[a-zA-Z0-9]+|\^[0-9]+|[a-zA-Z]\([a-zA-Z0-9,\s]+\)\s*=', s))

        if has_eq_num and (symbol_count >= 1 or '=' in s):
            return True
        if symbol_count >= 2 and len(s.split()) <= 15:
            return True
        if has_algebra and '=' in s and len(s.split()) <= 15:
            return True

        return False

    @staticmethod
    def _table_to_markdown(table_data: List[List[Optional[str]]]) -> str:
        """Convierte una matriz 2D de celdas en una tabla Markdown bien formateada."""
        if not table_data:
            return ""

        # Limpiar celdas nulas y normalizar saltos de línea dentro de celdas
        cleaned_rows: List[List[str]] = []
        for row in table_data:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cell_str = ""
                else:
                    # Reemplazar saltos de línea internos por espacios para preservar la fila Markdown
                    cell_str = str(cell).replace("\r\n", " ").replace("\n", " ").strip()
                    # Escapar barras verticales internas
                    cell_str = cell_str.replace("|", "&#124;")
                cleaned_row.append(cell_str)

            # Evitar filas totalmente vacías
            if any(c for c in cleaned_row):
                cleaned_rows.append(cleaned_row)

        if not cleaned_rows or len(cleaned_rows) < 2:
            return ""

        # Determinar número máximo de columnas válidas
        max_cols = max(len(r) for r in cleaned_rows)
        if max_cols < 2 or max_cols > 15:
            return ""

        # Rellenar filas cortas
        normalized_rows = []
        for r in cleaned_rows:
            if len(r) < max_cols:
                r.extend([""] * (max_cols - len(r)))
            normalized_rows.append(r)

        md_lines = []
        # Fila 1: Encabezados
        header = "| " + " | ".join(normalized_rows[0]) + " |"
        separator = "| " + " | ".join(["---"] * max_cols) + " |"
        md_lines.append(header)
        md_lines.append(separator)

        # Filas de datos
        for r in normalized_rows[1:]:
            row_line = "| " + " | ".join(r) + " |"
            md_lines.append(row_line)

        return "\n".join(md_lines)

    @staticmethod
    def _fallback_extract(file_bytes: bytes) -> str:
        """Fallback con pypdf cuando pdfplumber falla o para PDFs no estándar."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = PDFParser._clean_page_text(page_text)
                extracted_pages.append(f"<!-- [PAGE {i+1}] -->\n{cleaned}")
            return "\n\n".join(extracted_pages)
        except Exception:
            return ""

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
