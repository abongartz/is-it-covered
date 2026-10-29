# Is it covered?

Outil web qui détermine si un sinistre est couvert par un contrat d'assurance habitation (Luxembourg et Belgique),
en citant les clauses du contrat et en s'abstenant quand le contrat ne permet pas de conclure.

- **Application** : https://is-it-covered.streamlit.app/
- **Documentation** : [`docs/`](docs/README.md) (site public à venir)
- **Stratégie** : [`docs/strategie.md`](docs/strategie.md)

État : phase 0 (fondations) en cours. Voir [`docs/phases/`](docs/phases/).

## Démarrer en local

Prérequis : [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups                          # installe les dépendances figées
uv run streamlit run app/streamlit_app.py     # lance l'application
uv run pytest                                 # lance les tests
```
