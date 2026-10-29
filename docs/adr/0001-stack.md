# 0001 – Stack technique et gestion des dépendances

Statut : acceptée · Date : 2026-10-29

## Contexte

L'app doit être publique, gratuite à héberger et maintenue en 24 h environ. Le parsing des PDF est lourd et
tourne hors ligne ; l'hébergeur (Streamlit Community Cloud) dispose de peu de mémoire. Les dépendances doivent
être figées avec empreintes (attaques de la chaîne d'approvisionnement, cf. LiteLLM en mars 2026).

## Décision

- **Python 3.12**, paquet `isitcovered` en layout `src/`.
- **uv** pour l'environnement et le verrouillage (`uv.lock`).
- **Streamlit** pour l'interface, hébergée sur **Streamlit Community Cloud**.
- **Pydantic v2** pour tous les schémas ; **PyYAML** pour le manifeste et la taxonomie.
- **pytest** et **ruff** (lint et formatage), exécutés en CI (GitHub Actions, actions épinglées par SHA).
- **Groupes de dépendances séparés** : l'app n'installe que les dépendances du projet ; `dev` (tests, lint) et
  `ingestion` (parsing PDF) ne sont jamais installés sur l'hébergeur.
- L'hébergeur lit **`app/requirements.txt`**, exporté depuis `uv.lock` avec empreintes
  (`uv export --no-dev --no-emit-project`). Un test vérifie qu'il est synchronisé avec le verrou.
  Placé à côté du point d'entrée, il est prioritaire sur `pyproject.toml` pour l'hébergeur.
- Comme un fichier avec empreintes ne peut pas référencer le projet local, le point d'entrée de l'app ajoute
  `src/` au chemin d'import.

## Alternatives

- **Poetry** : plus lent, verrouillage moins pratique à exporter ; aucun avantage ici.
- **Laisser l'hébergeur lire `pyproject.toml`** : moins de contrôle sur ce qui est installé et sans empreintes.
- **Python 3.13** : possible, mais 3.12 a le support le plus large des bibliothèques de parsing.
- **Hugging Face Spaces, Render** : plus de ressources pour certains, mais Streamlit Community Cloud est le
  plus simple pour une app Streamlit liée à GitHub.

## Conséquences

- Toute modification de dépendance impose `uv lock` puis la régénération de `app/requirements.txt`.
- Le parsing ne peut jamais être appelé par l'app déployée (dépendance absente) ; ses sorties sont commitées en
  JSON.
