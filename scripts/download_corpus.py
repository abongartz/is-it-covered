"""Rebuild data/raw/ from data/manifest.yaml and verify every document's SHA-256.

Usage:
    uv run python scripts/download_corpus.py            # download missing documents
    uv run python scripts/download_corpus.py --check    # only verify local files, no network
"""

import argparse
import sys
from pathlib import Path

from isitcovered.ingestion.download import HashMismatchError, Status, sync_document
from isitcovered.models.corpus import Manifest

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "manifest.yaml")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--check", action="store_true", help="verify local files only, no download")
    args = parser.parse_args()

    manifest = Manifest.load(args.manifest)
    failures = 0
    for doc in manifest.documents:
        try:
            status = sync_document(doc, args.raw_dir, check_only=args.check)
        except HashMismatchError as exc:
            failures += 1
            print(f"ERROR {exc}", file=sys.stderr)
            continue
        except OSError as exc:
            failures += 1
            print(f"ERROR {doc.id}: download failed ({exc})", file=sys.stderr)
            continue
        if status is Status.MISSING:
            failures += 1
        print(f"{status:<10} {doc.id}")

    print(f"{len(manifest.documents) - failures}/{len(manifest.documents)} documents OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
