from pathlib import Path

import pytest

from isitcovered.models.corpus import Manifest
from isitcovered.models.sections import SectionTree

ROOT = Path(__file__).resolve().parents[1]
ETHIAS = "be-ethias-habitation-2025-03"


@pytest.fixture(scope="session")
def ethias_tree() -> SectionTree:
    """The approved section tree with its text: data/parsed/ if present, otherwise re-parsed from the PDF."""
    doc = Manifest.load(ROOT / "data" / "manifest.yaml").get(ETHIAS)
    parsed = ROOT / "data" / "parsed" / ETHIAS / "sections.json"
    if parsed.exists():
        tree = SectionTree.model_validate_json(parsed.read_text(encoding="utf-8"))
        if tree.source_sha256 == doc.sha256:
            return tree
    pytest.importorskip("pymupdf")
    from isitcovered.ingestion.parse import DEFAULT_PROFILE_BY_INSURER, PROFILES, parse_pdf

    pdf = ROOT / "data" / "raw" / doc.filename
    if not pdf.exists():
        pytest.skip("PDF not downloaded")
    tree, _ = parse_pdf(
        pdf,
        doc_id=doc.id,
        source_sha256=doc.sha256,
        profile=PROFILES[DEFAULT_PROFILE_BY_INSURER[doc.insurer]],
    )
    return tree
