"""Streamlit entry point."""

import sys
from pathlib import Path

# The host installs dependencies from app/requirements.txt, which does not include the project itself
# (hashed requirements cannot reference a local directory), so make src/ importable here.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Is it covered?", page_icon="🏠", layout="centered")

st.title("Is it covered?")
st.markdown(
    "Cet outil dira si un sinistre est couvert par un contrat d'assurance habitation "
    "(Luxembourg et Belgique), **en citant les clauses** du contrat, et répondra « indéterminé » "
    "quand le contrat ne permet pas de conclure."
)
st.info("Projet en construction : phase 0 (fondations). L'analyse de sinistres arrive en phase 1.")
st.markdown("[Code source et documentation](https://github.com/abongartz/is-it-covered)")
