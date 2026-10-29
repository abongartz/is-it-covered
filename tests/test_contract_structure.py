"""Committed structure of each parsed contract, and its reproducibility when the PDF is present."""

import json
import re
from pathlib import Path

import pytest
import yaml

from isitcovered.models.corpus import Manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT / "data" / "manifest.yaml")
PARSED = [d for d in MANIFEST.documents if (ROOT / "data" / "contracts" / d.id / "structure.json").exists()]


def load(doc_id: str, name: str) -> dict:
    return json.loads((ROOT / "data" / "contracts" / doc_id / name).read_text(encoding="utf-8"))


def walk(section: dict):
    yield section
    for child in section["children"]:
        yield from walk(child)


def test_first_contract_is_parsed():
    assert "be-ethias-habitation-2025-03" in [d.id for d in PARSED]


@pytest.mark.parametrize("doc", PARSED, ids=lambda d: d.id)
def test_structure_is_consistent(doc):
    structure = load(doc.id, "structure.json")
    assert structure["source_sha256"] == doc.sha256
    sections = [s for root in structure["sections"] for s in walk(root)]
    ids = [s["id"] for s in sections]
    assert len(ids) == len(set(ids))
    for section in sections:
        assert 1 <= section["page_start"] <= section["page_end"] <= structure["page_count"]
        for child in section["children"]:
            assert section["page_start"] <= child["page_start"] <= child["page_end"] <= section["page_end"]
            assert child["level"] > section["level"]


@pytest.mark.parametrize("doc", PARSED, ids=lambda d: d.id)
def test_toc_check_passes(doc):
    report = load(doc.id, "toc_check.json")
    assert report["ok"], [e for e in report["entries"] if e["problems"] and not e["accepted"]]


@pytest.mark.parametrize("doc", PARSED, ids=lambda d: d.id)
def test_tree_is_approved_for_the_current_parser(doc):
    """A human approved the tree on the annotated PDF; a new parser version needs a new one (ADR 0004)."""
    review = yaml.safe_load(
        (ROOT / "data" / "contracts" / doc.id / "review.yaml").read_text(encoding="utf-8")
    )
    assert review["approved_parser"] == load(doc.id, "structure.json")["parser"]
    assert review["reviewed_by"] and review["reviewed_at"]


@pytest.mark.parametrize("doc", PARSED, ids=lambda d: d.id)
def test_reparse_matches_committed_structure_and_loses_no_text(doc, tmp_path):
    """Needs the PDF (scripts/download_corpus.py) and the ingestion group."""
    pytest.importorskip("pymupdf")
    from isitcovered.ingestion.parse import DEFAULT_PROFILE_BY_INSURER, PROFILES, parse_pdf

    pdf = ROOT / "data" / "raw" / doc.filename
    if not pdf.exists():
        pytest.skip("PDF not downloaded")
    profile = PROFILES[DEFAULT_PROFILE_BY_INSURER[doc.insurer]]
    tree, rows = parse_pdf(pdf, doc_id=doc.id, source_sha256=doc.sha256, profile=profile)
    assert json.loads(json.dumps(tree.structure(), ensure_ascii=False)) == load(doc.id, "structure.json")

    # Every row of the document (after removing headers and page numbers) ends up in a block or a title.
    corpus = "\n".join(t for s in tree.walk() for t in [s.title, *(b.text for b in s.blocks)])
    prefix = re.compile(r"^(Chapitre\s+[IVXLC]+|Article\s+\d+|\d+(\.\d+)+\.?|[A-Z]\.)\s*")
    lost = [r.text for page in rows for r in page if prefix.sub("", r.text) not in corpus]
    assert lost == []

    # Drawn over the PDF, the tree covers every word except the removed page furniture (header, page numbers)
    # and the second line of wrapped titles (the heading box only spans the first line).
    import pymupdf

    from isitcovered.ingestion.annotate import annotate_pdf
    from isitcovered.ingestion.parse import extract_rows

    with pymupdf.open(pdf) as source:
        raw = extract_rows(source)
    kept = [{r.text for r in page} for page in rows]
    furniture = {
        w
        for page, texts in zip(raw, kept, strict=True)
        for r in page
        if r.text not in texts
        for w in r.text.split()
    }
    title_words = {w for s in tree.walk() for w in s.title.split()}
    report = annotate_pdf(pdf, tree, tmp_path / "annotated.pdf")
    assert [w for w in report.uncovered_words if w not in furniture | title_words] == []
    assert report.missed_italics == 0
