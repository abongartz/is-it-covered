"""Parse corpus PDFs into section trees and check them against their printed table of contents.

Usage:
    uv run --group ingestion python scripts/parse_contract.py [DOC_ID ...] [--profile NAME]

Writes, for each document:
    data/parsed/<doc_id>/sections.json    full tree with text (local only, git-ignored)
    data/parsed/<doc_id>/outline.md       readable outline with excerpts, for human review (local only)
    data/contracts/<doc_id>/structure.json  tree without text (committed)
    data/contracts/<doc_id>/toc_check.json  comparison with the printed table of contents (committed)

Discrepancies with the printed TOC that a human checked in the PDF (errors of the document itself) are
listed in data/contracts/<doc_id>/review.yaml and do not fail the check.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

from isitcovered.ingestion.download import sha256_file
from isitcovered.ingestion.parse import DEFAULT_PROFILE_BY_INSURER, PROFILES, parse_pdf
from isitcovered.ingestion.toc import check_toc, read_toc
from isitcovered.models.corpus import Manifest
from isitcovered.models.sections import Section, SectionTree

ROOT = Path(__file__).resolve().parents[1]
EXCERPT = 90


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def outline(tree: SectionTree) -> str:
    lines = [f"# {tree.doc_id}", "", f"Parser: `{tree.parser}` · {tree.page_count} pages", ""]

    def visit(section: Section) -> None:
        indent = "  " * (section.level - 1)
        number = f"{section.number} " if section.number else ""
        pages = f"p. {section.page_start}" + (
            f"–{section.page_end}" if section.page_end != section.page_start else ""
        )
        lines.append(
            f"{indent}- **{number}{section.title}** `{section.id}` ({pages}, {len(section.blocks)} blocs)"
        )
        for block in section.blocks:
            text = block.text if len(block.text) <= EXCERPT else block.text[:EXCERPT] + "…"
            lines.append(f"{indent}  - _{block.kind}, p. {block.page}_ : {text}")
        for child in section.children:
            visit(child)

    for section in tree.sections:
        visit(section)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("doc_ids", nargs="*", help="default: every document with a known layout profile")
    parser.add_argument("--profile", choices=sorted(PROFILES), help="override the layout profile")
    args = parser.parse_args()

    manifest = Manifest.load(ROOT / "data" / "manifest.yaml")
    docs = [manifest.get(i) for i in args.doc_ids] or [
        d for d in manifest.documents if d.insurer in DEFAULT_PROFILE_BY_INSURER
    ]
    failures = 0
    for doc in docs:
        pdf = ROOT / "data" / "raw" / doc.filename
        if not pdf.exists() or sha256_file(pdf) != doc.sha256:
            print(f"ERROR {doc.id}: missing or altered PDF, run scripts/download_corpus.py", file=sys.stderr)
            failures += 1
            continue
        profile = PROFILES[args.profile or DEFAULT_PROFILE_BY_INSURER[doc.insurer]]
        tree, rows = parse_pdf(pdf, doc_id=doc.id, source_sha256=doc.sha256, profile=profile)

        toc_section = next((s for s in tree.walk() if s.title == profile.toc_title), None)
        toc_rows = (
            [r for page in range(toc_section.page_start, toc_section.page_end + 1) for r in rows[page - 1]]
            if toc_section
            else []
        )
        review_path = ROOT / "data" / "contracts" / doc.id / "review.yaml"
        review = yaml.safe_load(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}
        entries = read_toc(toc_rows, ignore={profile.toc_title, "Page"})
        report = check_toc(entries, tree, accepted=review.get("toc_discrepancies") or {})

        parsed_dir = ROOT / "data" / "parsed" / doc.id
        write_json(parsed_dir / "sections.json", tree.model_dump(mode="json"))
        (parsed_dir / "outline.md").write_text(outline(tree), encoding="utf-8")
        write_json(ROOT / "data" / "contracts" / doc.id / "structure.json", tree.structure())
        write_json(ROOT / "data" / "contracts" / doc.id / "toc_check.json", report)

        sections = list(tree.walk())
        status = "OK" if report["ok"] else "MISMATCH"
        print(
            f"{doc.id}: {len(sections)} sections, {sum(len(s.blocks) for s in sections)} blocks; "
            f"TOC {status} ({report['toc_entries']} entries, {report['mismatches']} mismatches, "
            f"{len(report['extra_in_tree'])} extra)"
        )
        failures += not report["ok"]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
