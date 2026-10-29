"""Parser rules on a small synthetic PDF built with PyMuPDF (no corpus file needed)."""

import pytest

pymupdf = pytest.importorskip("pymupdf")

from isitcovered.ingestion.parse import PROFILES, parse_pdf  # noqa: E402
from isitcovered.ingestion.toc import TocEntry, check_toc, read_toc  # noqa: E402

WHITE = (1, 1, 1)


def text(page, x, y, s, font="helv", size=9.0, color=(0, 0, 0)):
    page.insert_text((x, y), s, fontname=font, fontsize=size, color=color)
    return x + pymupdf.get_text_length(s, fontname=font, fontsize=size)


def furniture(page, number):
    text(page, 283, 68, "Assurance Test", size=11)
    text(page, 540, 800, str(number), font="hebo", size=10)


@pytest.fixture
def parsed(tmp_path):
    doc = pymupdf.open()
    cover = doc.new_page()
    text(cover, 23, 100, "CONDITIONS GENERALES", font="hebo", size=30)

    p2 = doc.new_page()
    furniture(p2, 2)
    text(p2, 113, 100, "Chapitre I", font="hebo", size=14)
    text(p2, 198, 100, "Objet", font="hebo", size=14)
    text(p2, 113, 130, "Article 1", font="hebo", size=10, color=WHITE)
    text(p2, 198, 130, "Garanties", font="hebo", size=10, color=WHITE)
    text(p2, 85, 160, "1.1.", font="hebo", size=10)
    text(p2, 113, 160, "L'incendie", font="hebo", size=10)
    x = text(p2, 113, 178, "Nous", font="heit")
    text(p2, x, 178, " couvrons les dommages causes")
    text(p2, 113, 189, "par le feu :")
    text(p2, 113, 205, "- le vol ;")
    text(p2, 113, 220, "- la tentative de vol.")
    text(p2, 113, 245, "A. Principe", font="hebo")
    text(p2, 113, 262, "Texte du principe*.")
    text(p2, 283, 790, "* Indice ABEX 789", font="heit", size=8)

    p3 = doc.new_page()
    furniture(p3, 3)
    text(p3, 113, 100, "Chapitre II Lexique", font="hebo", size=14)
    text(p3, 113, 130, "Incendie", font="hebo")
    text(p3, 127, 143, "Destruction par des flammes.")

    back = doc.new_page()
    text(back, 100, 700, "Contact : 04 000 00 00")

    path = tmp_path / "test.pdf"
    doc.save(path)
    return parse_pdf(
        path, doc_id="be-test-habitation-2025-01", source_sha256="0" * 64, profile=PROFILES["ethias-2025"]
    )


def test_section_hierarchy(parsed):
    tree, _ = parsed
    assert [(s.id, s.kind, s.level) for s in tree.walk()] == [
        ("couverture", "front", 1),
        ("ch-i", "chapter", 1),
        ("art-1", "article", 2),
        ("art-1.1", "subarticle", 3),
        ("art-1.1/A", "heading", 4),
        ("ch-ii", "chapter", 1),
        ("def-incendie", "term", 2),
        ("quatrieme-de-couverture", "front", 1),
    ]
    sections = {s.id: s for s in tree.walk()}
    assert sections["ch-i"].title == "Objet"
    assert sections["art-1"].title == "Garanties"
    assert sections["art-1.1"].title == "L'incendie"
    assert sections["ch-ii"].title == "Lexique"
    assert (sections["ch-i"].page_start, sections["ch-i"].page_end) == (2, 2)


def test_blocks_kinds_text_and_italics(parsed):
    tree, _ = parsed
    sections = {s.id: s for s in tree.walk()}
    blocks = sections["art-1.1"].blocks
    assert [b.kind for b in blocks] == ["paragraph", "list_item", "list_item"]
    assert blocks[0].text == "Nous couvrons les dommages causes par le feu :"
    assert blocks[0].italic == ["Nous"]
    assert blocks[0].page == 2
    assert [b.kind for b in sections["art-1.1/A"].blocks] == ["paragraph", "footnote"]
    assert sections["def-incendie"].blocks[0].text == "Destruction par des flammes."


def test_page_furniture_is_removed(parsed):
    tree, _ = parsed
    texts = [b.text for s in tree.walk() for b in s.blocks]
    assert not any("Assurance Test" in t for t in texts)
    assert not any(t.strip().isdigit() for t in texts)


def test_structure_has_no_text(parsed):
    tree, _ = parsed
    dumped = str(tree.structure())
    assert "Destruction par des flammes" not in dumped
    assert "Lexique" in dumped  # titles are kept


class FakeRow:
    def __init__(self, text: str):
        self.text = text


def test_read_toc_handles_wrapped_entries():
    rows = [
        FakeRow(t)
        for t in [
            "Table des matières",
            "Page",
            "Chapitre I - Objet 2",
            "Article 1 : Garanties",
            "très longues 2",
        ]
    ]
    assert read_toc(rows, ignore={"Table des matières", "Page"}) == [
        TocEntry("chapter", "I", "Objet", 2),
        TocEntry("article", "1", "Garanties très longues", 2),
    ]


def test_check_toc_reports_and_accepts_discrepancies(parsed):
    tree, _ = parsed
    entries = [TocEntry("chapter", "I", "Objet", 2), TocEntry("article", "1", "Garanties", 3)]
    report = check_toc(entries, tree)
    assert not report["ok"]
    assert report["entries"][1]["problems"] == ["page"]
    assert report["extra_in_tree"] == ["ch-ii"]

    entries.append(TocEntry("chapter", "II", "Lexique", 3))
    report = check_toc(entries, tree, accepted={"art-1": "erreur du sommaire imprimé"})
    assert report["ok"]
    assert report["accepted_discrepancies"] == 1
