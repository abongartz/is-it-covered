"""Download the corpus documents listed in the manifest and verify their SHA-256.

A document whose source no longer matches the recorded hash is never overwritten: a changed source means a new
edition, which must be added to the manifest next to the old one.
"""

import hashlib
import urllib.request
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

from isitcovered.models.corpus import ManifestDocument

USER_AGENT = "is-it-covered/0.1 (+https://github.com/abongartz/is-it-covered)"
TIMEOUT_S = 60

Fetcher = Callable[[str], bytes]


class Status(StrEnum):
    PRESENT = "present"  # already in raw_dir with the right hash
    DOWNLOADED = "downloaded"
    MISSING = "missing"  # check mode only


class HashMismatchError(Exception):
    def __init__(self, doc: ManifestDocument, actual: str, where: str):
        self.doc, self.actual, self.where = doc, actual, where
        super().__init__(
            f"{doc.id}: SHA-256 mismatch for the {where} (expected {doc.sha256}, got {actual}). "
            + (
                "The source has probably changed: add the new edition as a new manifest entry."
                if where == "source"
                else "Delete the local file and download it again."
            )
        )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def http_fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return response.read()


def sync_document(
    doc: ManifestDocument, raw_dir: Path, *, fetch: Fetcher = http_fetch, check_only: bool = False
) -> Status:
    """Make sure raw_dir holds the document with its recorded hash; raise HashMismatchError otherwise."""
    target = raw_dir / doc.filename
    if target.exists():
        actual = sha256_file(target)
        if actual != doc.sha256:
            raise HashMismatchError(doc, actual, "local file")
        return Status.PRESENT
    if check_only:
        return Status.MISSING

    data = fetch(str(doc.source_url))
    actual = sha256_bytes(data)
    if actual != doc.sha256:
        raise HashMismatchError(doc, actual, "source")
    raw_dir.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    partial.write_bytes(data)
    partial.replace(target)
    return Status.DOWNLOADED
