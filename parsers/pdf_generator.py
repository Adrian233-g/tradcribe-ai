import io
import os
import re
from typing import List, Tuple
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, KeepTogether, HRFlowable, PageBreak, Image as RLImage
)
from reportlab.platypus.paraparser import ParaParser
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas personalizado de dos pasadas para calcular y numerar 'Página X de Y'."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 8)
        self.setFillColor(HexColor("#64748b"))

        page_w, page_h = A4

        # Encabezado superior
        self.setStrokeColor(HexColor("#d1d5db"))
        self.setLineWidth(0.4)
        self.line(54, page_h - 38, page_w - 54, page_h - 38)
        self.drawString(54, page_h - 34, "Tradcribe AI · Traducción Académica y Técnica")

        # Pie de página inferior
        self.line(54, 42, page_w - 42, 42)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(page_w - 54, 30, page_text)
        self.drawString(54, 30, "Documento traducido y formateado automáticamente")
        self.restoreState()


class PDFGenerator:
    """Generador de PDFs académicos de alta fidelidad visual — estilo journal/paper con protección total contra errores de sintaxis XML."""

    @classmethod
    def _is_valid_reportlab_xml(cls, text: str) -> bool:
        """Verifica si el texto XML es completamente válido y no provocará un ParseError en ReportLab."""
        if not text:
            return True
        try:
            parser = ParaParser()
            parser.parse(f"<para>{text}</para>")
            return True
        except Exception:
            return False

    @classmethod
    def _escape_plain(cls, text: str) -> str:
        """Escapa texto plano a entidades XML básicas."""
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def _format_inline_markdown(cls, text: str) -> str:
        """Convierte negritas, cursivas y código inline a etiquetas HTML compatibles con ReportLab y valida balance XML."""
        if not text:
            return ""

        # Escapar caracteres XML antes de procesar etiquetas
        escaped = cls._escape_plain(text)

        # Código inline: `codigo`
        formatted = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9" color="#7c3aed">\1</font>', escaped)

        # Negrita cursiva triple: ***texto***
        formatted = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', formatted)

        # Negrita: **texto** o __texto__
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', formatted)
        formatted = re.sub(r'__(.+?)__', r'<b>\1</b>', formatted)

        # Cursiva: *texto* o _texto_ (evitando asteriscos aislados)
        formatted = re.sub(r'(?<!\*)\*([^\*\s][^\*]*?)\*(?!\*)', r'<i>\1</i>', formatted)
        formatted = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<i>\1</i>', formatted)

        # Validar si el XML resultante es seguro para ReportLab
        if cls._is_valid_reportlab_xml(formatted):
            return formatted

        # Si hay etiquetas cruzadas o inválidas (e.g. <i><b></i></b>), limpiar etiquetas huérfanas
        cleaned = re.sub(r'<(b|i|font[^>]*)>\s*</\1>', '', formatted)
        if cls._is_valid_reportlab_xml(cleaned):
            return cleaned

        # Si aún es inválido, eliminar todas las etiquetas HTML para garantizar que el PDF siempre se compile sin errores
        return re.sub(r'<[^>]+>', '', formatted)

    @classmethod
    def _create_safe_paragraph(cls, formatted_text: str, raw_text: str, style: ParagraphStyle) -> Paragraph:
        """Crea un párrafo garantizando que ningún error de parseo XML detenga la exportación."""
        try:
            return Paragraph(formatted_text, style)
        except Exception:
            return Paragraph(cls._escape_plain(raw_text), style)

    @classmethod
    def create_pdf_from_markdown(cls, markdown_text: str, document_title: str = "Artículo Traducido") -> bytes:
        """Transforma texto Markdown en un PDF con tipografía académica profesional (A4, Times New Roman)."""
        buffer = io.BytesIO()

        page_w, page_h = A4

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=25 * mm,
            rightMargin=25 * mm,
            topMargin=25 * mm,
            bottomMargin=25 * mm,
            title=document_title,
            author="Tradcribe AI"
        )

        styles = getSampleStyleSheet()

        # Paleta de colores — estilo journal académico
        primary_color = HexColor("#111827")     # Gray 900 — texto título
        secondary_color = HexColor("#1e3a5f")   # Dark blue — secciones principales
        accent_color = HexColor("#2563eb")      # Blue 600 — subsecciones
        body_color = HexColor("#1f2937")        # Gray 800 — body text
        bg_code = HexColor("#f9fafb")           # Gray 50 — fondo código
        border_code = HexColor("#e5e7eb")       # Gray 200

        usable_width = page_w - 50 * mm

        # ── Estilos tipográficos estilo paper académico ──

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Times-Bold',
            fontSize=17,
            leading=21,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=14,
            spaceBefore=6
        )

        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName='Times-Bold',
            fontSize=13.5,
            leading=16.5,
            textColor=secondary_color,
            spaceBefore=14,
            spaceAfter=5,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName='Times-Bold',
            fontSize=12,
            leading=15,
            textColor=accent_color,
            spaceBefore=12,
            spaceAfter=4,
            keepWithNext=True
        )

        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName='Times-Bold',
            fontSize=11,
            leading=13.5,
            textColor=primary_color,
            spaceBefore=10,
            spaceAfter=3,
            keepWithNext=True
        )

        h4_style = ParagraphStyle(
            'CustomH4',
            parent=styles['Heading3'],
            fontName='Times-BoldItalic',
            fontSize=10.5,
            leading=13,
            textColor=HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=10.5,
            leading=14,
            textColor=body_color,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            firstLineIndent=0
        )

        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=body_style,
            leftIndent=18,
            firstLineIndent=-12,
            spaceAfter=3,
            alignment=TA_LEFT
        )

        nested_bullet_style = ParagraphStyle(
            'NestedBullet',
            parent=bullet_style,
            leftIndent=36,
            firstLineIndent=-12,
            spaceAfter=2
        )

        quote_style = ParagraphStyle(
            'CustomQuote',
            parent=body_style,
            fontName='Times-Italic',
            leftIndent=24,
            rightIndent=24,
            textColor=HexColor("#4b5563"),
            spaceBefore=6,
            spaceAfter=6
        )

        code_style = ParagraphStyle(
            'CustomCode',
            fontName='Courier',
            fontSize=8.5,
            leading=11,
            textColor=HexColor("#1e293b")
        )

        equation_style = ParagraphStyle(
            'EquationStyle',
            parent=styles['Normal'],
            fontName='Times-Italic',
            fontSize=10.5,
            leading=14,
            textColor=HexColor("#0f172a"),
            alignment=TA_CENTER
        )

        image_caption_style = ParagraphStyle(
            'ImageCaption',
            parent=styles['Normal'],
            fontName='Times-Italic',
            fontSize=9,
            leading=12,
            textColor=HexColor("#4b5563"),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=8
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            fontName='Times-Bold',
            fontSize=9.5,
            leading=12,
            textColor=HexColor("#ffffff"),
            alignment=TA_CENTER
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            fontName='Times-Roman',
            fontSize=9,
            leading=11.5,
            textColor=body_color,
            alignment=TA_LEFT
        )

        # ── Construir story ──

        story = []
        lines = markdown_text.split("\n")
        i = 0
        n = len(lines)
        is_first_heading = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        while i < n:
            raw_line = lines[i]
            line = raw_line.strip()

            if not line:
                i += 1
                continue

            # Ignorar comentarios de página
            if line.startswith("<!-- [PAGE") and line.endswith("-->"):
                i += 1
                continue

            # ── Bloques de Imágenes: ![Caption](path) ──
            img_match = re.match(r'^!\[(.*?)\]\((.*?)\)', line)
            if img_match:
                caption = img_match.group(1).strip()
                raw_path = img_match.group(2).strip()

                # Resolver ruta absoluta o relativa
                resolved_path = raw_path
                if not os.path.isabs(resolved_path):
                    candidate = os.path.join(base_dir, resolved_path)
                    if os.path.exists(candidate):
                        resolved_path = candidate

                if os.path.exists(resolved_path) and os.path.isfile(resolved_path):
                    try:
                        with PILImage.open(resolved_path) as pil_im:
                            orig_w, orig_h = pil_im.size

                        if orig_w > 0 and orig_h > 0:
                            aspect = orig_w / orig_h
                            max_w = usable_width
                            max_h = 240.0

                            scaled_w = min(orig_w * 0.75, max_w)
                            scaled_h = scaled_w / aspect

                            if scaled_h > max_h:
                                scaled_h = max_h
                                scaled_w = max_h * aspect

                            rl_img = RLImage(resolved_path, width=scaled_w, height=scaled_h)
                            cap_p = cls._create_safe_paragraph(cls._format_inline_markdown(f"<i>{caption}</i>"), caption, image_caption_style)

                            # Agrupar imagen y caption juntos para evitar cortes de página
                            story.append(KeepTogether([
                                Spacer(1, 4),
                                rl_img,
                                Spacer(1, 2),
                                cap_p,
                                Spacer(1, 6)
                            ]))
                            i += 1
                            continue
                    except Exception:
                        pass

                # Fallback si no se puede cargar la imagen física: mostrar caja con caption
                cap_box = cls._create_safe_paragraph(f"🖼️ <b>[Figura]:</b> {cls._format_inline_markdown(caption)}", caption, image_caption_style)
                story.append(cap_box)
                i += 1
                continue

            # ── Bloques de Ecuaciones: $$ ... $$ ──
            if line.startswith("$$"):
                eq_lines = []
                if line == "$$":
                    i += 1
                    while i < n and not lines[i].strip().startswith("$$"):
                        eq_lines.append(lines[i].strip())
                        i += 1
                    if i < n and lines[i].strip().startswith("$$"):
                        i += 1
                else:
                    # Ecuación en una sola línea: $$ formula $$
                    eq_content = re.sub(r'^\$\$\s*|\s*\$\$$', '', line)
                    eq_lines.append(eq_content)
                    i += 1

                full_eq = " ".join(eq_lines).strip()
                if full_eq:
                    formatted_eq = cls._format_inline_markdown(full_eq)
                    eq_p = cls._create_safe_paragraph(formatted_eq, full_eq, equation_style)
                    eq_table = Table([[eq_p]], colWidths=[usable_width])
                    eq_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f8fafc")),
                        ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 12),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ]))
                    story.append(Spacer(1, 3))
                    story.append(eq_table)
                    story.append(Spacer(1, 6))
                continue

            # ── Bloques de Código: ``` ... ``` ──
            if line.startswith("```"):
                code_lines = []
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                if i < n and lines[i].strip().startswith("```"):
                    i += 1
                code_text = "\n".join(code_lines)

                code_p = Preformatted(code_text, code_style)
                code_table = Table(
                    [[code_p]],
                    colWidths=[usable_width]
                )
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_code),
                    ('BOX', (0, 0), (-1, -1), 0.5, border_code),
                    ('TOPPADDING', (0, 0), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(code_table)
                story.append(Spacer(1, 8))
                continue

            # ── Tablas Markdown: | col1 | col2 | ──
            if line.startswith("|") and line.endswith("|"):
                table_lines = []
                raw_table_lines = []
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    t_line = lines[i].strip()
                    raw_table_lines.append(t_line)
                    # Ignorar separador | --- | --- |
                    if not re.match(r'^\|[\s\-:]+([\|][\s\-:]+)+\|$', t_line):
                        cells = [c.strip().replace("&#124;", "|") for c in t_line.strip("|").split("|")]
                        table_lines.append(cells)
                    i += 1

                if table_lines:
                    num_cols = max(len(row) for row in table_lines)
                    # Solo renderizar como Table de ReportLab si la tabla es válida y segura (2 a 15 columnas, >= 2 filas)
                    if 2 <= num_cols <= 15 and len(table_lines) >= 2:
                        norm_rows = []
                        for row_idx, row in enumerate(table_lines):
                            row_cells = []
                            is_head = (row_idx == 0)
                            cell_st = table_header_style if is_head else table_cell_style
                            for col_idx in range(num_cols):
                                val = row[col_idx] if col_idx < len(row) else ""
                                formatted_val = cls._format_inline_markdown(val)
                                row_cells.append(cls._create_safe_paragraph(formatted_val, val, cell_st))
                            norm_rows.append(row_cells)

                        col_w = usable_width / num_cols
                        pdf_table = Table(norm_rows, colWidths=[col_w] * num_cols)
                        pdf_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#1e3a5f")),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#d1d5db")),
                            ('TOPPADDING', (0, 0), (-1, -1), 5),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f9fafb")]),
                        ]))
                        story.append(Spacer(1, 4))
                        story.append(pdf_table)
                        story.append(Spacer(1, 10))
                    else:
                        # Fallback seguro: renderizar como párrafos de texto formateados
                        for r_line in raw_table_lines:
                            if not re.match(r'^\|[\s\-:]+([\|][\s\-:]+)+\|$', r_line):
                                clean_r = r_line.strip("|").replace("|", " · ")
                                story.append(cls._create_safe_paragraph(cls._format_inline_markdown(clean_r), clean_r, body_style))
                continue

            # ── Líneas horizontales ──
            if re.match(r'^[-*_]{3,}\s*$', line):
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", thickness=0.75, color=HexColor("#d1d5db"), spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            # ── Encabezados ──
            if line.startswith("#### "):
                heading_raw = line[5:].strip()
                text_content = cls._format_inline_markdown(heading_raw)
                story.append(cls._create_safe_paragraph(text_content, heading_raw, h4_style))
            elif line.startswith("### "):
                heading_raw = line[4:].strip()
                text_content = cls._format_inline_markdown(heading_raw)
                story.append(cls._create_safe_paragraph(text_content, heading_raw, h3_style))
            elif line.startswith("## "):
                heading_raw = line[3:].strip()
                text_content = cls._format_inline_markdown(heading_raw)
                story.append(cls._create_safe_paragraph(text_content, heading_raw, h2_style))
            elif line.startswith("# "):
                heading_raw = line[2:].strip()
                text_content = cls._format_inline_markdown(heading_raw)
                if is_first_heading:
                    story.append(cls._create_safe_paragraph(text_content, heading_raw, title_style))
                    story.append(HRFlowable(width="60%", thickness=1.2, color=HexColor("#2563eb"), spaceBefore=2, spaceAfter=14))
                    is_first_heading = False
                else:
                    story.append(cls._create_safe_paragraph(text_content, heading_raw, h1_style))
                    story.append(HRFlowable(width="100%", thickness=0.6, color=HexColor("#d1d5db"), spaceBefore=2, spaceAfter=6))
            # ── Citas o Notas ──
            elif line.startswith("> "):
                quote_lines = [line[2:].strip()]
                while i + 1 < n and lines[i + 1].strip().startswith("> "):
                    i += 1
                    quote_lines.append(lines[i].strip()[2:].strip())
                raw_quote = " ".join(quote_lines)
                text_content = cls._format_inline_markdown(raw_quote)
                # Cita con barra lateral
                quote_p = cls._create_safe_paragraph(text_content, raw_quote, quote_style)
                quote_table = Table(
                    [[quote_p]],
                    colWidths=[usable_width - 6]
                )
                quote_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f3f4f6")),
                    ('LEFTPADDING', (0, 0), (-1, -1), 14),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LINEBEFOREDECOR', (0, 0), (0, -1), 3, accent_color),
                ]))
                story.append(quote_table)
                story.append(Spacer(1, 6))
            # ── Listas con viñeta ──
            elif re.match(r'^[\*\-]\s+', line):
                item_text = re.sub(r'^[\*\-]\s+', '', line)
                text_content = f"• {cls._format_inline_markdown(item_text)}"
                story.append(cls._create_safe_paragraph(text_content, f"• {item_text}", bullet_style))
            # ── Listas con sub-viñeta (indentación) ──
            elif re.match(r'^\s{2,}[\*\-]\s+', raw_line):
                item_text = re.sub(r'^\s+[\*\-]\s+', '', raw_line)
                text_content = f"◦ {cls._format_inline_markdown(item_text)}"
                story.append(cls._create_safe_paragraph(text_content, f"◦ {item_text}", nested_bullet_style))
            # ── Listas numeradas ──
            elif re.match(r'^\d+\.\s+', line):
                prefix_m = re.match(r'^(\d+\.)\s+', line)
                prefix = prefix_m.group(1) if prefix_m else ""
                item_text = line[len(prefix_m.group(0)):] if prefix_m else line
                text_content = f"<b>{prefix}</b> {cls._format_inline_markdown(item_text)}"
                story.append(cls._create_safe_paragraph(text_content, f"{prefix} {item_text}", bullet_style))
            # ── Párrafo estándar ──
            else:
                text_content = cls._format_inline_markdown(line)
                story.append(cls._create_safe_paragraph(text_content, line, body_style))

            i += 1

        # Construir el documento con el Canvas numerado
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
