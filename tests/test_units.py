from isitcovered.ingestion.definitions import lexicon_definitions
from isitcovered.ingestion.units import UnitPlan, build_units
from isitcovered.models.sections import Section, SectionTree, TextBlock

BBOX = (0.0, 0.0, 10.0, 10.0)


def section(id, kind, title, number=None, level=1, blocks=(), children=()) -> Section:
    return Section(
        id=id,
        kind=kind,
        number=number,
        title=title,
        level=level,
        page_start=1,
        page_end=1,
        bbox=BBOX,
        blocks=[TextBlock(kind="paragraph", text=t, page=1, bbox=BBOX) for t in blocks],
        children=list(children),
    )


def small_tree() -> SectionTree:
    art1 = section("art-1", "article", "Biens", "1", 2, ["Texte de l'article 1."])
    art2 = section(
        "art-2",
        "article",
        "Garanties",
        "2",
        2,
        children=[
            section("art-2.1", "subarticle", "L'incendie", "2.1", 3),
            section("art-2.2", "subarticle", "Le vol", "2.2", 3, ["Vol avec effraction.", "Exclusion."]),
        ],
    )
    art3 = section("art-3", "article", "Option", "3", 2, ["Accordée si mentionnée aux CP."])
    art3.children = [
        section("art-3.1", "subarticle", "Qu'est-ce qui est assuré ?", "3.1", 3, ["Le contenu."])
    ]
    ch1 = section("ch-i", "chapter", "Garanties", "I", 1, ["Ce chapitre vaut pour tout."], [art1, art2, art3])
    lexicon = section(
        "ch-ii",
        "chapter",
        "Lexique",
        "II",
        1,
        children=[section("def-vol", "term", "Vol", level=2, blocks=["Soustraction."])],
    )
    return SectionTree(
        doc_id="doc", source_sha256="0" * 64, parser="test", page_count=1, sections=[ch1, lexicon]
    )


def test_units_follow_the_plan():
    units = build_units(small_tree(), UnitPlan(("ch-i",), frozenset({"art-2"})))
    assert [u.id for u in units] == ["art-1", "art-2.1", "art-2.2", "art-3"]


def test_unit_carries_context_titles_and_references():
    units = {u.id: u for u in build_units(small_tree(), UnitPlan(("ch-i",), frozenset({"art-2"})))}
    fire = units["art-2.1"]
    assert fire.section_path == ["Chapitre I – Garanties", "Article 2 – Garanties", "2.1 – L'incendie"]
    assert fire.sibling_titles == ["2.2 – Le vol"]
    assert [(b.ref, b.context) for b in fire.blocks] == [("ch-i#1", True), ("art-2.1#0", False)]
    assert fire.block("art-2.1#0").text == "L'incendie"

    option = units["art-3"]
    assert [b.ref for b in option.blocks] == ["ch-i#1", "art-3#0", "art-3#1", "art-3.1#0", "art-3.1#1"]
    assert option.section_ids() == ["art-3", "art-3.1"]
    assert "[art-3#1] (p. 1) Accordée si mentionnée aux CP." in option.render()


def test_lexicon_becomes_definitions():
    [definition] = lexicon_definitions(small_tree())
    assert definition.term == "Vol" and definition.text == "Soustraction." and definition.origin == "lexicon"
    assert definition.source.quotes[0].block_ref == "def-vol#1"
    assert definition.source.section_path == ["Chapitre II – Lexique", "Vol"]


# --- the real contract (needs data/parsed/ or the PDF) ---------------------------------------------------


def test_ethias_has_28_units(ethias_tree):
    units = build_units(ethias_tree)
    ids = [u.id for u in units]
    assert ids == [
        "art-1",
        "art-2",
        *(f"art-3.{n}" for n in range(1, 21)),
        *(f"art-{n}" for n in range(4, 10)),
    ]


def test_ethias_units_include_headers_and_title_blocks(ethias_tree):
    units = {u.id: u for u in build_units(ethias_tree)}
    # Sub-articles without text of their own are citable through their title.
    assert [b.ref for b in units["art-3.1"].blocks] == ["art-3.1#0"]
    assert units["art-3.1"].block("art-3.1#0").text == "L’incendie"
    # art. 3.20 has text only in its subdivisions A and B.
    assert {"art-3.20/A#1", "art-3.20/B#1"} <= {b.ref for b in units["art-3.20"].blocks}
    # The CP-subscription sentence heading art. 4 is part of its unit; ch. IV's scope sentence is context.
    assert "conditions particulières" in units["art-4"].block("art-4#1").text
    assert units["art-7"].block("ch-iv#1").context
    assert "catastrophes naturelles" in units["art-7"].block("ch-iv#1").text
    # art. 4.4 holds the exclusion relevant to the bicycle example.
    assert "parties communes" in units["art-4"].block("art-4.4#4").text


def test_ethias_lexicon_has_53_definitions(ethias_tree):
    definitions = lexicon_definitions(ethias_tree)
    assert len(definitions) == 53
    assert len({d.term for d in definitions}) == 53
    fire = next(d for d in definitions if d.term == "Incendie")
    assert "flammes" in fire.text and fire.source.quotes[0].block_ref == "def-incendie#1"
