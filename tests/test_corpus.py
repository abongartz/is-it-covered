from pathlib import Path

import pytest
from pydantic import ValidationError

from isitcovered.ingestion.download import HashMismatchError, Status, sha256_bytes, sync_document
from isitcovered.models.corpus import Manifest, ManifestDocument

ROOT = Path(__file__).resolve().parents[1]
CONTENT = b"%PDF-1.7 fake contract"


def make_doc(**overrides) -> ManifestDocument:
    fields = {
        "id": "be-acme-habitation-2025-03",
        "country": "BE",
        "insurer": "Acme",
        "product": "Habitation",
        "doc_type": "cg",
        "language": "fr",
        "edition_ref": "X-1 03/25",
        "edition_date": "2025-03",
        "source_url": "https://example.com/cg.pdf",
        "sha256": sha256_bytes(CONTENT),
        "retrieved_at": "2026-10-29",
        "pages": 1,
    }
    return ManifestDocument.model_validate(fields | overrides)


def fetch_ok(url: str) -> bytes:
    return CONTENT


def fetch_forbidden(url: str) -> bytes:
    raise AssertionError("no network call expected")


def test_project_manifest_is_valid():
    manifest = Manifest.load(ROOT / "data" / "manifest.yaml")
    assert manifest.documents
    assert manifest.get("be-ethias-habitation-2025-03").country == "BE"


def test_manifest_rejects_duplicate_ids():
    doc = make_doc().model_dump(mode="json")
    with pytest.raises(ValidationError, match="duplicate"):
        Manifest.model_validate({"documents": [doc, doc]})


@pytest.mark.parametrize(
    "overrides", [{"id": "Ethias habitation"}, {"sha256": "abc"}, {"edition_date": "03/25"}, {"extra": 1}]
)
def test_manifest_document_rejects_invalid_fields(overrides):
    with pytest.raises(ValidationError):
        make_doc(**overrides)


def test_downloads_missing_document(tmp_path):
    doc = make_doc()
    assert sync_document(doc, tmp_path, fetch=fetch_ok) is Status.DOWNLOADED
    assert (tmp_path / doc.filename).read_bytes() == CONTENT
    assert sync_document(doc, tmp_path, fetch=fetch_forbidden) is Status.PRESENT


def test_changed_source_is_not_written(tmp_path):
    doc = make_doc()
    with pytest.raises(HashMismatchError, match="new edition"):
        sync_document(doc, tmp_path, fetch=lambda url: b"another edition")
    assert not any(tmp_path.iterdir())


def test_corrupted_local_file_is_not_overwritten(tmp_path):
    doc = make_doc()
    (tmp_path / doc.filename).write_bytes(b"corrupted")
    with pytest.raises(HashMismatchError, match="local file"):
        sync_document(doc, tmp_path, fetch=fetch_forbidden)
    assert (tmp_path / doc.filename).read_bytes() == b"corrupted"


def test_check_mode_never_downloads(tmp_path):
    assert sync_document(make_doc(), tmp_path, fetch=fetch_forbidden, check_only=True) is Status.MISSING
