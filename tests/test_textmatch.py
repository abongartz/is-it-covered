import pytest

from isitcovered.textmatch import find_quote, normalize, source_passage

BLOCK = "• locataire, nous assurons votre responsabilité de locataire ou d’occupant et/ ou le contenu."


def test_normalization():
    assert normalize("L’Incendie « total » – vu") == 'l\'incendie"total"-vu'
    assert normalize("a b\nc") == "abc"
    assert normalize("ﬁn") == "fin"  # NFKC ligature


@pytest.mark.parametrize(
    "quote",
    [
        "votre responsabilité de locataire ou d'occupant",  # straight apostrophe
        "VOTRE RESPONSABILITÉ de locataire",  # case
        "d’occupant et/ou le contenu",  # line-break artefact "et/ ou"
        "nous   assurons\nvotre responsabilité",  # whitespace
    ],
)
def test_quotes_match_despite_typography(quote):
    assert find_quote(BLOCK, quote).ok


def test_the_source_wording_is_returned():
    assert source_passage(BLOCK, "responsabilité de locataire ou d'occupant") == (
        "responsabilité de locataire ou d’occupant"
    )
    assert source_passage(BLOCK, "d'occupant et/ou le contenu.") == "d’occupant et/ ou le contenu."


def test_invented_or_altered_quotes_are_rejected():
    assert find_quote(BLOCK, "nous assurons votre responsabilité de propriétaire").status == "not_found"
    assert source_passage(BLOCK, "le contenu volé dans la cave") is None


def test_short_quotes_must_cover_the_whole_text():
    assert find_quote(BLOCK, "locataire").status == "too_short"
    assert find_quote("L’incendie", "L'incendie").ok  # a whole title
    assert find_quote("La foudre", "la foudre").ok
    assert find_quote(BLOCK, "  ").status == "empty"
