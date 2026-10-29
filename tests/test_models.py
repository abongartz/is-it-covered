from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from isitcovered.models.extraction import Condition, ContractExtraction, Exclusion, Guarantee, Quote, Source
from isitcovered.models.taxonomy import OTHER, Taxonomy

ROOT = Path(__file__).resolve().parents[1]


def source(ref="art-4.4#4") -> Source:
    quote = Quote(block_ref=ref, text="texte", page=15, bbox=(0, 0, 1, 1))
    return Source(doc_id="doc", section_id=quote.section_id, section_path=["Article 4"], quotes=[quote])


def extraction(exclusion_scope="specific", targets=("doc/g/theft",)) -> ContractExtraction:
    guarantee = Guarantee(
        id="doc/g/theft",
        name="Vol",
        section_id="art-4",
        kind="optional",
        cp_optional=True,
        source=source("art-4#1"),
    )
    trigger = Condition(id="doc/x/common-areas/t1", kind="location", text="parties communes", source=source())
    exclusion = Exclusion(
        id="doc/x/common-areas",
        scope=exclusion_scope,
        guarantee_ids=list(targets),
        triggers=[trigger],
        source=source(),
    )
    return ContractExtraction(
        doc_id="doc",
        source_sha256="0" * 64,
        parser="test",
        model="anthropic/claude-sonnet-5-5",
        prompt_version="abc",
        created_at=datetime.now(UTC),
        guarantees=[guarantee],
        exclusions=[exclusion],
    )


def test_a_consistent_extraction_validates():
    assert extraction().guarantee("doc/g/theft").cp_optional


@pytest.mark.parametrize(
    ("scope", "targets"),
    [("specific", ()), ("specific", ("doc/g/missing",)), ("general", ("doc/g/theft",))],
)
def test_exclusion_targets_are_checked(scope, targets):
    with pytest.raises(ValidationError):
        extraction(scope, targets)


def test_block_references_are_checked():
    with pytest.raises(ValidationError):
        Quote(block_ref="art-4.4", text="x", page=1, bbox=(0, 0, 1, 1))
    assert Quote(block_ref="art-3.20/A#0", text="x", page=1, bbox=(0, 0, 1, 1)).section_id == "art-3.20/A"


def test_taxonomy_v1():
    taxonomy = Taxonomy.load(ROOT / "data" / "taxonomy.yaml")
    perils = [c for c in taxonomy.active_concepts if c.id != OTHER]
    assert 13 <= len(perils) <= 17
    for concept in perils:
        assert concept.description and concept.examples and concept.includes, concept.id
    assert {"bicycles", "garden_furniture", "contents", "building"} <= {f.id for f in taxonomy.facets.assets}
    assert {"common_areas", "garden_outdoor"} <= {f.id for f in taxonomy.facets.locations}
    assert {f.id for f in taxonomy.facets.status} == {"owner", "tenant", "other_occupant"}


def test_taxonomy_rejects_duplicates_and_dangling_deprecations():
    data = Taxonomy.load(ROOT / "data" / "taxonomy.yaml").model_dump()
    duplicated = {**data, "concepts": [*data["concepts"], data["concepts"][0]]}
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(duplicated)
    dangling = {
        **data,
        "concepts": [{**data["concepts"][0], "deprecated_by": "nowhere"}, *data["concepts"][1:]],
    }
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(dangling)
