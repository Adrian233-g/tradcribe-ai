import io
import re
from typing import List, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, KeepTogether, HRFlowable, PageBreak
)
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
    """Generador de PDFs académicos de alta fidelidad visual — estilo journal/paper."""

    @classmethod
    def _format_inline_markdown(cls, text: str) -> str:
        """Convierte negritas, cursivas y código inline a etiquetas HTML compatibles con ReportLab."""
        if not text:
            return ""

        # Escapar caracteres XML antes de procesar etiquetas
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Código inline: `codigo`
        text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9" color="#7c3aed">\1</font>', text)

        # Negrita: **texto** o __texto__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

        # Cursiva: *texto* o _texto_
        text = re.sub(r'\*([^\*]+)\*', r'<i>\1</i>', text)
        text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<i>\1</i>', text)

        return text

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
            fontSize=18,
            leading=22,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=16,
            spaceBefore=8
        )

        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName='Times-Bold',
            fontSize=14,
            leading=17,
            textColor=secondary_color,
            spaceBefore=16,
            spaceAfter=6,
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
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    t_line = lines[i].strip()
                    # Ignorar separador | --- | --- |
                    if not re.match(r'^\|[\s\-:]+([\|][\s\-:]+)+\|$', t_line):
                        cells = [c.strip() for c in t_line.strip("|").split("|")]
                        table_lines.append(cells)
                    i += 1

                if table_lines:
                    num_cols = max(len(row) for row in table_lines)
                    norm_rows = []
                    for row_idx, row in enumerate(table_lines):
                        row_cells = []
                        is_head = (row_idx == 0)
                        cell_st = table_header_style if is_head else table_cell_style
                        for col_idx in range(num_cols):
                            val = row[col_idx] if col_idx < len(row) else ""
                            formatted_val = cls._format_inline_markdown(val)
                            row_cells.append(Paragraph(formatted_val, cell_st))
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
                continue

            # ── Líneas horizontales ──
            if re.match(r'^[-*_]{3,}\s*$', line):
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", thickness=0.75, color=HexColor("#d1d5db"), spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            # ── Encabezados ──
            if line.startswith("#### "):
                text_content = cls._format_inline_markdown(line[5:].strip())
                story.append(Paragraph(text_content, h4_style))
            elif line.startswith("### "):
                text_content = cls._format_inline_markdown(line[4:].strip())
                story.append(Paragraph(text_content, h3_style))
            elif line.startswith("## "):
                text_content = cls._format_inline_markdown(line[3:].strip())
                story.append(Paragraph(text_content, h2_style))
            elif line.startswith("# "):
                text_content = cls._format_inline_markdown(line[2:].strip())
                if is_first_heading:
                    story.append(Paragraph(text_content, title_style))
                    story.append(HRFlowable(width="60%", thickness=1.2, color=HexColor("#2563eb"), spaceBefore=2, spaceAfter=14))
                    is_first_heading = False
                else:
                    story.append(Paragraph(text_content, h1_style))
                    story.append(HRFlowable(width="100%", thickness=0.6, color=HexColor("#d1d5db"), spaceBefore=2, spaceAfter=6))
            # ── Citas o Notas ──
            elif line.startswith("> "):
                quote_lines = [line[2:].strip()]
                while i + 1 < n and lines[i + 1].strip().startswith("> "):
                    i += 1
                    quote_lines.append(lines[i].strip()[2:].strip())
                text_content = cls._format_inline_markdown(" ".join(quote_lines))
                # Cita con barra lateral
                quote_p = Paragraph(text_content, quote_style)
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
                story.append(Paragraph(text_content, bullet_style))
            # ── Listas con sub-viñeta (indentación) ──
            elif re.match(r'^\s{2,}[\*\-]\s+', raw_line):
                item_text = re.sub(r'^\s+[\*\-]\s+', '', raw_line)
                text_content = f"◦ {cls._format_inline_markdown(item_text)}"
                story.append(Paragraph(text_content, nested_bullet_style))
            # ── Listas numeradas ──
            elif re.match(r'^\d+\.\s+', line):
                prefix_m = re.match(r'^(\d+\.)\s+', line)
                prefix = prefix_m.group(1) if prefix_m else ""
                item_text = line[len(prefix_m.group(0)):] if prefix_m else line
                text_content = f"<b>{prefix}</b> {cls._format_inline_markdown(item_text)}"
                story.append(Paragraph(text_content, bullet_style))
            # ── Párrafo estándar ──
            else:
                text_content = cls._format_inline_markdown(line)
                story.append(Paragraph(text_content, body_style))

            i += 1

        # Construir el documento con el Canvas numerado
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
