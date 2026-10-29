# Phase 0 – Plan d'action

Statut : **terminé le 2026-10-29** · Coût LLM de la phase : **0 €** (aucun appel)

Attendus : `phase0.md`. Ce plan découpe la phase en 4 incréments ; chacun se termine par des tests verts,
un commit sur `main` et une app déployée qui fonctionne.

## Décisions proposées (à valider)

| # | Sujet | Proposition | Alternatives | ADR |
| --- | --- | --- | --- | --- |
| D1 | Stack | Python 3.12, uv (`uv.lock`), Streamlit, Pydantic v2, pytest, ruff | Poetry ; Python 3.13 | 0001 |
| D2 | Dépendances déployées | Groupes séparés : l'app n'installe que `streamlit`, `pydantic`, `pyyaml` ; le parseur est dans un groupe `ingestion` jamais installé sur l'hébergeur. `requirements.txt` exporté depuis `uv.lock` avec empreintes, synchronisation vérifiée en CI | Laisser l'hébergeur lire `pyproject.toml` (moins de contrôle sur ce qui est installé) | 0001 |
| D3 | Premier contrat | **Ethias – CG Assurance Habitation (BE, FR)** : public, complet (36 p.), vol et incendie présents, sommaire imprimé exploitable | AXA Belgium Confort Habitation (PDF de 2017, 68 Ko, probablement partiel) | 0002 |
| D4 | Parseur | **PyMuPDF** : léger, déterministe, coordonnées au niveau du mot, police et italique disponibles (utile pour les termes définis) ; hiérarchie reconstruite par règles (numérotation + typographie) | Docling (meilleur sur mises en page complexes, mais lourd : PyTorch, modèles) ; repli si PyMuPDF échoue sur un contrat | 0003 |
| D5 | Flux git | Une branche par incrément, fusion dans `main` quand la CI est verte | Commits directs sur `main` | – |

Point de licence : PyMuPDF est sous AGPL. Sans conséquence ici (dépôt public, parseur hors ligne), noté dans l'ADR 0003.

## Incrément 1 – Squelette déployé

1. `pyproject.toml` (layout `src/`, paquet `isitcovered`), `.python-version`, `uv.lock`, `requirements.txt` exporté.
2. Arborescence de `CLAUDE.md` : dossiers et paquets vides (`__init__.py` / `.gitkeep`).
3. `.streamlit/config.toml` : `client.showErrorDetails = false`, barre d'outils minimale, thème.
   `.streamlit/secrets.toml.example` (le vrai fichier reste ignoré par git).
4. `app/streamlit_app.py` : page d'accueil minimale en français (le projet, l'état d'avancement, liens).
5. CI GitHub Actions : `uv sync --locked`, `ruff check`, `pytest`, contrôle de `requirements.txt`.
6. `README.md` court ; `docs/README.md` (index structuré, vide) ; `docs/adr/0001-stack.md`.
7. **Action utilisateur** : créer l'app sur Streamlit Community Cloud (dépôt, branche `main`,
   `app/streamlit_app.py`, Python 3.12), renseigner les secrets ; je fournis la marche à suivre.

Vérification : l'URL publique répond ; le README pointe dessus ; la CI est verte.

## Incrément 2 – Premier contrat

1. `data/manifest.yaml`, validé par un modèle Pydantic : identifiant de document
   (`be-ethias-habitation-<édition>`), pays, assureur, produit, type (`cg`), langue, référence et date d'édition
   imprimées dans le document, URL source, SHA-256, date de récupération, nombre de pages.
2. `src/isitcovered/ingestion/download.py` + `scripts/download_corpus.py` :
   télécharge chaque document absent de `data/raw/`, vérifie l'empreinte, échoue explicitement si elle diffère
   (une source modifiée = nouvelle édition à ajouter au manifeste, jamais un écrasement). Option `--check`.
3. Tests sans réseau : validation du manifeste, vérification d'empreinte (fichier fictif), refus d'écrasement.
4. `docs/adr/0002-premier-contrat.md`.

Vérification « machine vierge » : clone dans un dossier temporaire, `uv sync`, script lancé, `data/raw/`
reconstruit avec la bonne empreinte.

## Incrément 3 – Parsing structurel

1. Modèle `Section` (`src/isitcovered/models/`) : identifiant stable dérivé du chemin (`art-3.2`), numéro,
   titre, niveau, pages de début et de fin, blocs de texte (texte, page, coordonnées), enfants.
2. `src/isitcovered/ingestion/parse.py` + `scripts/parse_contract.py` :
   - extraction des blocs et des polices avec PyMuPDF ;
   - suppression des en-têtes et pieds de page répétés (« Assurance Habitation », numéro de page) ;
   - titres détectés par numérotation et typographie : Chapitre > Article > sous-article (`1.1.`) > niveau suivant ;
   - lexique (chapitre VII) découpé en une entrée par terme ;
   - marquage des passages en italique (termes définis), conservé pour la phase 1.
3. Sortie `data/contracts/<doc_id>/sections.json` avec métadonnées : `doc_id`, SHA-256 du PDF, version du parseur,
   date de génération.
4. **Contrôle contre le sommaire** : le sommaire imprimé (page 4) est lu et comparé automatiquement à l'arbre
   (titres et numéros de page des chapitres et articles) ; le résultat est enregistré dans un rapport.
5. Plan lisible (`scripts/show_sections.py` → Markdown) pour la **relecture humaine** ; écarts corrigés ou
   documentés comme limites.
6. Tests : règles de détection sur de petits PDF générés dans les tests ; cohérence du JSON commité
   (schéma valide, pages croissantes, aucun bloc perdu, identifiants uniques).
7. `docs/features/parsing.md` (méthode, pourquoi, limites) ; `docs/adr/0003-parseur-pdf.md`.
8. Option (petite) : l'app affiche le corpus (manifeste) et l'arbre de sections du contrat, lus depuis les JSON.

Vérification : contrôle du sommaire sans écart non expliqué ; arbre relu et validé par l'utilisateur.

## Incrément 4 – Clôture

- `CLAUDE.md` : section « Commandes » complétée, arborescence ajustée si besoin.
- `docs/README.md` à jour (fonctionnalité parsing, ADR 0001 à 0003).
- Revue des critères de fin ci-dessous ; statut du plan passé à « terminé ».

## Critères de fin de phase → preuve

| Critère | Preuve |
| --- | --- |
| L'URL publique de l'app répond | Lien dans le README, vérifié après le dernier déploiement |
| Arbre relu, conforme au sommaire | `toc_check.json` (29 entrées, un écart expliqué) ; approbation sur le PDF annoté consignée dans `review.yaml` (ADR 0004) |
| `data/raw/` reconstruit sur machine vierge | Procédure de clone temporaire exécutée et consignée ci-dessous |
| Page parsing dans `docs/features/`, au moins un ADR | `docs/features/parsing.md`, ADR 0001 à 0004 |

## Actions attendues de l'utilisateur

- Valider ce plan (décisions D1 à D5).
- Autoriser le premier `git push` vers le dépôt public `abongartz/is-it-covered`.
- Créer l'app sur Streamlit Community Cloud et renseigner les secrets (incrément 1).
- Relire l'arbre de sections du contrat (incrément 3).
- Pour la phase 1 (rappel) : clé API avec limite de dépense réglée dans la console du fournisseur.

## Risques

| Risque | Parade |
| --- | --- |
| L'hébergeur n'importe pas le paquet `src/` (installation avec empreintes) | Vérifié dès l'incrément 1 ; repli : chemin ajouté au démarrage de l'app |
| Le site Ethias bloque les téléchargements automatisés ou change d'URL | En-tête `User-Agent` explicite ; échec clair ; URL mise à jour dans le manifeste |
| Ethias publie une nouvelle édition à la même URL | L'empreinte diffère → erreur explicite, nouvelle entrée au manifeste |
| Mise en page (listes, tableaux, titres sur deux lignes) mal découpée | Contrôle contre le sommaire, relecture, Docling en repli |

## Journal

- 2026-10-29 : plan rédigé. Repérage du PDF Ethias : 36 pages, pas de signets PDF, sommaire imprimé page 4
  (7 chapitres, 21 articles), termes définis en italique, lexique au chapitre VII.
- 2026-10-29 : incrément 1 fusionné (PR #1) ; app déployée sur https://is-it-covered.streamlit.app/
  (Python 3.12, `app/requirements.txt` lu par l'hébergeur).
- 2026-10-29 : incrément 2. Référence d'édition imprimée en dernière page : `1252-050 • 03/25`.
  Vérification « machine vierge » : clone dans un dossier temporaire, `uv sync --locked` (sans groupes
  optionnels), `download_corpus.py` puis `--check` → 1/1 document téléchargé, empreinte conforme.
- 2026-10-29 : incrément 2 fusionné (PR #2).
- 2026-10-29 : incrément 3. **Écart au plan** : l'arbre avec le texte intégral republierait les CG ; il est
  écrit dans `data/parsed/` (ignoré par git) et seule la structure sans texte est commitée
  (`data/contracts/<doc>/structure.json`), avec `toc_check.json` et `review.yaml` (ADR 0003).
  Résultat Ethias : 7 chapitres, 21 articles, 98 sous-articles, 59 termes du lexique, 641 blocs ; sommaire
  conforme sur 29 entrées, un écart dû au document (article 20 annoncé p. 29, commence p. 30). Aucune rangée de
  texte perdue (test). L'app affiche le corpus et l'arbre. **En attente : relecture de l'arbre par l'utilisateur.**
- 2026-10-29 : incrément 3 fusionné (PR #3).
- 2026-10-29 : incrément 4. **Écart au plan** : la relecture se fait sur le PDF original annoté (chaque titre et
  bloc encadré en couleur, `scripts/parse_contract.py`) plutôt que sur le plan textuel. Décision consignée dans
  l'ADR 0004 : règles de parsing rédigées par l'agent et approuvées par un humain sur ce PDF, approbation liée à
  la version du parseur (test) ; parsing entièrement automatique et import de CG reportés (« si le temps le
  permet »). **Arbre Ethias approuvé par l'utilisateur** le 2026-10-29 (`pymupdf-rules/ethias-2025@1`).
  Point reporté par l'utilisateur : parades supplémentaires contre les erreurs d'extraction des objets typés
  (phase 1 garde ce que prévoit la stratégie).
