"""Finding a quoted passage in a source text, tolerant of typography (ADR 0010).

Both texts are normalized before comparison: Unicode NFKC, typographic apostrophes, quotes and dashes mapped
to their ASCII form, case folded, and **all whitespace removed** (which also absorbs line-break artefacts such
as "et/ ou"). A table maps each normalized character back to its position in the original text, so that the
passage returned is always the source's own wording, never the quoted one.
"""

import unicodedata
from dataclasses import dataclass
from typing import Literal

MIN_QUOTE_CHARS = 15  # normalized length; shorter quotes must cover the whole source text (e.g. a title)

_CHAR_MAP = str.maketrans(
    {
        "’": "'",  # ’
        "‘": "'",  # ‘
        "ʼ": "'",  # ʼ
        "«": '"',  # «
        "»": '"',  # »
        "“": '"',  # “
        "”": '"',  # ”
        "–": "-",  # –
        "—": "-",  # —
        "‑": "-",  # non-breaking hyphen
    }
)


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalized text and, for each of its characters, the index of the source character it comes from."""
    chars: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        for out in unicodedata.normalize("NFKC", ch).translate(_CHAR_MAP).casefold():
            if out.isspace():
                continue
            chars.append(out)
            origin.append(i)
    return "".join(chars), origin


def normalize(text: str) -> str:
    return normalize_with_map(text)[0]


@dataclass(frozen=True)
class QuoteMatch:
    status: Literal["ok", "not_found", "too_short", "empty"]
    start: int = 0  # in the original source text
    end: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def find_quote(source: str, quote: str) -> QuoteMatch:
    """Locate `quote` in `source`; the first occurrence wins."""
    norm_source, origin = normalize_with_map(source)
    norm_quote = normalize(quote)
    if not norm_quote:
        return QuoteMatch("empty")
    if len(norm_quote) < MIN_QUOTE_CHARS and norm_quote != norm_source:
        return QuoteMatch("too_short")
    pos = norm_source.find(norm_quote)
    if pos < 0:
        return QuoteMatch("not_found")
    return QuoteMatch("ok", origin[pos], origin[pos + len(norm_quote) - 1] + 1)


def source_passage(source: str, quote: str) -> str | None:
    """The source's own text for `quote`, or None if it is not a valid quote of `source`."""
    match = find_quote(source, quote)
    return source[match.start : match.end] if match.ok else None
