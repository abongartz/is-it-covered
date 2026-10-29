"""Committed structure of each parsed contract, and its reproducibility when the PDF is present."""

import json
import re
from pathlib import Path

import pytest

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
def test_reparse_matches_committed_structure_and_loses_no_text(doc):
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
