"""Annotated copy of a parsed PDF: the section tree drawn over the original pages, for human approval.

Each heading and each text block gets a colored box and its identifier in the margin; italic runs are
underlined; words that belong to no block and no heading are outlined, so dropped text is visible.
Offline only (PyMuPDF). The output contains the full contract text and is never published.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from isitcovered.models.sections import SectionTree

Color = tuple[float, float, float]

SECTION_COLORS: dict[str, Color] = {
    "chapter": (0.85, 0.10, 0.10),
    "article": (0.50, 0.20, 0.75),
    "subarticle": (0.85, 0.20, 0.60),
    "heading": (0.00, 0.55, 0.55),
    "term": (0.70, 0.60, 0.00),
    "front": (0.30, 0.30, 0.30),
}
BLOCK_COLORS: dict[str, Color] = {
    "paragraph": (0.20, 0.45, 0.90),
    "list_item": (0.15, 0.65, 0.30),
    "label": (0.95, 0.55, 0.10),
    "footnote": (0.55, 0.35, 0.25),
}
ITALIC_COLOR: Color = (0.85, 0.10, 0.10)
UNCOVERED_COLOR: Color = (0.90, 0.00, 0.00)
MARGIN = (2, 96)  # x range of the identifiers written in the left margin
DASHES = "[1.5] 0"

SECTION_LEGEND = {
    "chapter": "Chapitre",
    "article": "Article",
    "subarticle": "Sous-article (« 4.2. »)",
    "heading": "Intitulé non numéroté ou subdivision lettrée (« A. »)",
    "term": "Terme du lexique (une section par terme défini)",
    "front": "Pages liminaires (sommaire, préambule)",
}
BLOCK_LEGEND = {
    "paragraph": "Paragraphe",
    "list_item": "Élément de liste (puce, tiret, a), 1°)",
    "label": "Phrase en gras qui n'est pas un titre",
    "footnote": "Note de bas de page (conservée)",
}


@dataclass
class AnnotationReport:
    uncovered_words: list[str]  # words of the PDF in no block and no heading (page furniture, wrapped titles)
    missed_italics: int  # italic runs that could not be located on the page


def annotate_pdf(pdf_path: Path, tree: SectionTree, out_path: Path) -> AnnotationReport:
    with pymupdf.open(pdf_path) as pdf:
        words = [page.get_text("words") for page in pdf]  # before drawing, so labels are not counted
        covered: list[list[pymupdf.Rect]] = [[] for _ in range(pdf.page_count)]
        missed_italics = 0

        for section in tree.walk():
            page = pdf[section.page_start - 1]
            color = SECTION_COLORS[section.kind]
            rect = pymupdf.Rect(section.bbox) + (-2, -1, 2, 1)
            page.draw_rect(rect, color=color, fill=color, fill_opacity=0.18, width=1.2)
            _margin_text(page, rect.y0, f"{section.id}\n{section.kind}", color, bold=True)
            covered[section.page_start - 1].append(rect)
            for i, block in enumerate(section.blocks, 1):
                page = pdf[block.page - 1]
                color = BLOCK_COLORS[block.kind]
                rect = pymupdf.Rect(block.bbox) + (-1.5, -1, 1.5, 1)
                page.draw_rect(rect, color=color, fill=color, fill_opacity=0.10, width=0.7)
                _margin_text(page, rect.y0, f"{section.id} #{i} · {block.kind}", color)
                covered[block.page - 1].append(rect)
                for run in block.italic:
                    hits = page.search_for(run, clip=rect + (-1, -1, 1, 1))
                    missed_italics += not hits
                    for hit in hits:
                        page.draw_line(hit.bl + (0, 0.8), hit.br + (0, 0.8), color=ITALIC_COLOR, width=0.9)

        uncovered = []
        for page, page_words, rects in zip(pdf, words, covered, strict=True):
            for word in page_words:
                box = pymupdf.Rect(word[:4])
                center = (box.tl + box.br) / 2
                if not any(center in r for r in rects):
                    uncovered.append(word[4])
                    page.draw_rect(
                        box + (-0.5, -0.5, 0.5, 0.5), color=UNCOVERED_COLOR, width=0.8, dashes=DASHES
                    )

        report = AnnotationReport(uncovered_words=uncovered, missed_italics=missed_italics)
        _legend_page(pdf, tree, report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pdf.save(out_path, garbage=3, deflate=True)
    return report


def _margin_text(page: pymupdf.Page, y: float, text: str, color: Color, bold: bool = False) -> None:
    page.insert_textbox(
        pymupdf.Rect(MARGIN[0], y, MARGIN[1], y + 20),
        text,
        fontsize=5.5,
        fontname="hebo" if bold else "helv",
        color=color,
        align=pymupdf.TEXT_ALIGN_RIGHT,
    )


def _legend_page(pdf: pymupdf.Document, tree: SectionTree, report: AnnotationReport) -> None:
    page = pdf.new_page(0, width=pdf[0].rect.width, height=pdf[0].rect.height)
    sections = list(tree.walk())
    y = 60.0

    def line(text: str, size: float, bold: bool = False, gap: float = 20) -> None:
        nonlocal y
        page.insert_text((50, y), text, fontsize=size, fontname="hebo" if bold else "helv")
        y += gap

    def entry(color: Color, name: str, description: str, dashed: bool = False) -> None:
        nonlocal y
        swatch = pymupdf.Rect(50, y - 9, 80, y + 2)
        if dashed:
            page.draw_rect(swatch, color=color, width=0.8, dashes=DASHES)
        else:
            page.draw_rect(swatch, color=color, fill=color, fill_opacity=0.15, width=1)
        page.insert_text((90, y), name, fontsize=9.5, fontname="hebo", color=color)
        page.insert_textbox(pymupdf.Rect(200, y - 9, 545, y + 30), description, fontsize=8.5, fontname="helv")
        y += 26

    line(f"Arbre de sections parsé · {tree.doc_id}", 14, bold=True, gap=18)
    line(
        f"Parseur : {tree.parser} · {len(sections)} sections · {sum(len(s.blocks) for s in sections)} blocs",
        9,
    )
    y += 10
    line("Titres de section (cadre épais, identifiant en marge en gras)", 10.5, bold=True)
    for kind, description in SECTION_LEGEND.items():
        entry(SECTION_COLORS[kind], kind, description)
    y += 10
    line("Blocs de texte (cadre fin, « section #n · type » en marge)", 10.5, bold=True)
    for kind, description in BLOCK_LEGEND.items():
        entry(BLOCK_COLORS[kind], kind, description)
    y += 10
    line("Autres marques", 10.5, bold=True)
    page.draw_line((52, y - 2), (78, y - 2), color=ITALIC_COLOR, width=1.2)
    page.insert_text((90, y), "italique", fontsize=9.5, fontname="hebo", color=ITALIC_COLOR)
    page.insert_textbox(
        pymupdf.Rect(200, y - 9, 545, y + 30),
        "Passage en italique relevé dans le bloc (chez Ethias : terme défini au lexique)",
        fontsize=8.5,
        fontname="helv",
    )
    y += 26
    entry(
        UNCOVERED_COLOR,
        "hors arbre",
        "Mot qui n'appartient à aucun bloc ni titre : en-tête courant ou numéro de page retirés, "
        "ou suite d'un titre sur deux lignes (seule la première ligne du titre est encadrée)",
        dashed=True,
    )
    y += 14
    page.insert_textbox(
        pymupdf.Rect(50, y, 545, y + 60),
        f"Contrôles : {len(report.uncovered_words)} mots hors arbre ; {report.missed_italics} passages en "
        "italique non retrouvés sur la page. Document local, non publié (texte intégral des CG).",
        fontsize=8.5,
        fontname="helv",
    )
