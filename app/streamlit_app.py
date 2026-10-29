"""Streamlit entry point."""

import sys
from pathlib import Path

# The host installs dependencies from app/requirements.txt, which does not include the project itself
# (hashed requirements cannot reference a local directory), so make src/ importable here.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import json  # noqa: E402

import streamlit as st  # noqa: E402

from isitcovered.models.corpus import Manifest  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
KIND_LABELS = {
    "chapter": "chapitres",
    "article": "articles",
    "subarticle": "sous-articles",
    "term": "définitions",
}
NUMBER_PREFIXES = {"chapter": "Chapitre ", "article": "Article "}
DOC_TYPES = {"cg": "Conditions générales", "ipid": "IPID"}

st.set_page_config(page_title="Is it covered?", page_icon="🏠", layout="centered")

st.title("Is it covered?")
st.markdown(
    "Cet outil dira si un sinistre est couvert par un contrat d'assurance habitation "
    "(Luxembourg et Belgique), **en citant les clauses** du contrat, et répondra « indéterminé » "
    "quand le contrat ne permet pas de conclure."
)
st.info("Projet en construction : fondations en place (phase 0). L'analyse de sinistres arrive en phase 1.")
st.markdown("[Code source et documentation](https://github.com/abongartz/is-it-covered)")


def walk(section: dict):
    yield section
    for child in section["children"]:
        yield from walk(child)


def outline_markdown(structure: dict) -> str:
    lines = []
    for section in (s for root in structure["sections"] for s in walk(root)):
        prefix = NUMBER_PREFIXES.get(section["kind"], "")
        number = f"{prefix}{section['number']} – " if section["number"] else ""
        pages = f"p. {section['page_start']}"
        if section["page_end"] != section["page_start"]:
            pages += f"–{section['page_end']}"
        lines.append(f"{'  ' * (section['level'] - 1)}- {number}{section['title']} ({pages})")
    return "\n".join(lines)


st.header("Corpus")
st.caption("Contrats téléchargés depuis leur source publique et découpés en sections (texte non republié).")
for doc in Manifest.load(DATA / "manifest.yaml").documents:
    structure_path = DATA / "contracts" / doc.id / "structure.json"
    st.subheader(f"{doc.insurer} – {doc.product} ({doc.country})")
    st.markdown(
        f"{DOC_TYPES[doc.doc_type]}, édition `{doc.edition_ref}` · {doc.pages} pages · "
        f"[source]({doc.source_url}) · récupéré le {doc.retrieved_at:%d/%m/%Y}"
    )
    if not structure_path.exists():
        st.caption("Pas encore découpé en sections.")
        continue
    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    sections = [s for root in structure["sections"] for s in walk(root)]
    counts = {label: sum(1 for s in sections if s["kind"] == kind) for kind, label in KIND_LABELS.items()}
    st.markdown(" · ".join(f"**{n}** {label}" for label, n in counts.items()))
    with st.expander("Arbre des sections"):
        st.markdown(outline_markdown(structure))
