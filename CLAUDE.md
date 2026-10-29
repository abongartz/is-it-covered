# CLAUDE.md

Règles et carte du projet, relues à chaque prompt. Ce fichier ne contient **ni décisions ni explications** :
- une décision va dans un ADR (`docs/adr/`) ;
- une explication de *comment* ou *pourquoi* quelque chose est implémenté va dans `docs/features/`.
Taille : viser moins de 150 lignes, **ne jamais dépasser 200**. S'il grossit, déplacer du contenu vers `docs/`.

## Le projet

Outil web qui détermine si un sinistre est couvert par un contrat d'assurance habitation (Luxembourg et Belgique),
en citant les clauses et en s'abstenant quand le contrat ne permet pas de conclure.
Exercice technique pour un recruteur. Livrables : app publique (Streamlit Community Cloud), dépôt GitHub public,
site de documentation public (GitHub Pages). Budget LLM total : **20 € maximum**.

Document de référence (stratégie validée) : `docs/strategie.md`. Le relire avant toute décision structurante.

## Principes non négociables

1. **Le LLM juge des conditions élémentaires, le code construit le verdict.** L'agrégation
   (`couvert` / `non couvert` / `indéterminé`) est déterministe, en Python, jamais rédigée par un LLM.
2. **Toute affirmation sur un contrat cite sa source** (document, page, texte exact), et chaque citation est
   vérifiée par programme contre le texte source avant d'être affichée.
3. **L'abstention est une réponse.** Un fait manquant ou une clause ambiguë donne `indéterminé`, avec ce qui manque.
   Ne trouver aucune garantie ne vaut **jamais** `non couvert` sans clause explicite.
4. **Les définitions appartiennent à leur contrat.** Ne jamais fusionner ni normaliser les définitions entre contrats.
5. **La taxonomie oriente, elle ne définit pas.** Les concepts servent à sélectionner les garanties ; le sens
   juridique vient toujours du texte du contrat analysé.
6. **Une demande = un pipeline isolé.** Un message est d'abord découpé en demandes (couple événement, bien) ;
   chaque demande a ses propres faits et garanties candidates.
7. **La mise en forme ne change jamais un verdict.** Le compositeur assemble des verdicts déjà calculés ; aucune
   consigne utilisateur ne supprime les citations ni ne transforme un `indéterminé`.

## Toujours livrable

- `main` est toujours déployable ; l'URL publique de l'app doit fonctionner après chaque objectif terminé.
- Ne jamais pousser sur `main` du code qui casse l'app, les tests ou la construction du site.
- **Définition de « terminé »** pour tout objectif : code poussé, tests verts, app déployée et fonctionnelle,
  `docs/` et site public à jour, ADR ajouté si un choix a été fait.

## Documentation

- **`docs/README.md` est l'index** : il associe chaque fonctionnalité à son fichier dans `docs/features/` et
  liste les ADR. Pour travailler sur une fonctionnalité : lire l'index, puis le fichier de la fonctionnalité
  et les ADR liés **avant** de modifier le code ; les mettre à jour **après**.
- **`docs/features/<fonctionnalite>.md`** : comment et pourquoi c'est implémenté, limites connues.
- **`docs/adr/NNNN-titre-court.md`** : une décision par fichier (contexte, décision, alternatives, conséquences).
  Numérotation continue, jamais réutilisée ; une décision remplacée est marquée « remplacée par NNNN ».
- **`docs/phases/`** : `phaseN.md` = attendus d'une phase (fournis, ne pas modifier sans accord) ;
  `phaseN-plan.md` = plan d'action rédigé par l'agent au début de la phase, tenu à jour pendant la phase.
- **Site public (`site/`)** : tenu à jour à chaque fonctionnalité. **Aucun chiffre écrit à la main** :
  résultats d'évaluation, taxonomie, corpus et traces d'exemples sont lus depuis des JSON produits par le code
  (`eval/results.json`, `data/…`). Chaque bloc chiffré affiche date, commit et modèle.
- Langue : documentation, interface et site en **français** ; code, identifiants et commits en **anglais**.

## Sécurité et données

- **Clés API** (la nôtre comme celles des utilisateurs) : jamais sur disque, dans l'URL, les journaux, les messages
  d'erreur ni une clé de cache. Notre clé via `st.secrets` ; celle de l'utilisateur en mémoire de session seulement.
  `client.showErrorDetails = false` ; journaux HTTP des SDK désactivés.
- **CP importées** (données personnelles) : masquer les données personnelles avant tout appel LLM, ne rien
  conserver (ni fichier ni texte), ne garder que les champs du formulaire validés par l'utilisateur.
  Fournisseurs LLM autorisés uniquement s'ils ne réutilisent pas les données (plan gratuit Mistral exclu).
- **CG importées par l'utilisateur** : traitées pour la session uniquement, jamais stockées ni partagées.
- **Aucun PDF de CG brut dans le dépôt** (`data/raw/` est ignoré par git) : manifeste + script de téléchargement.
- **Dépendances figées** avec fichier de verrouillage et empreintes ; ne pas ajouter de dépendance sans raison.
- Aucun point d'entrée générique vers un fournisseur LLM : le serveur n'exécute que les prompts du projet.

## LLM et coûts

- Tout appel passe par l'abstraction `LLMClient` (`src/isitcovered/llm/`). **Aucun SDK de fournisseur importé
  ailleurs**, sauf le code de batch dans `src/isitcovered/ingestion/`.
- Sorties structurées validées par Pydantic ; `max_tokens` toujours fixé ; version de modèle figée (jamais
  d'alias `latest`) ; température 0 pour l'ingestion.
- Mettre au point un prompt en synchrone sur **un seul** contrat avant toute exécution sur le corpus.
- **Demander l'accord de l'utilisateur avant** : un batch, une exécution sur tout le corpus, un passage complet
  d'évaluation, ou toute action dont le coût estimé dépasse 0,50 €. Annoncer le coût estimé.
- Chaque appel enregistre tokens et coût estimé ; les plafonds (session, IP, global journalier) ne sont jamais
  contournés, y compris en développement sur l'app déployée.

## Données du corpus

- Un document = (pays, assureur, produit, édition). Le manifeste `data/manifest.yaml` enregistre aussi l'URL
  source, l'empreinte SHA-256, la référence et la date d'édition, la date de récupération.
- **Ne jamais écraser une édition** : une nouvelle édition s'ajoute à côté de l'ancienne.
- Taxonomie : `data/taxonomy.yaml`, identifiants stables, jamais renommés ni réutilisés (dépréciation avec
  renvoi). Toute modification de concept = un ADR.

## Arborescence

À tenir à jour à chaque ajout de dossier ou de module important.

```
.
├── CLAUDE.md
├── README.md                    # présentation courte, liens app / site / docs
├── pyproject.toml, uv.lock      # dépendances figées
├── .streamlit/config.toml       # thème, showErrorDetails=false (secrets.toml ignoré par git)
├── app/                         # interface Streamlit (pages, composants d'affichage)
├── src/isitcovered/
│   ├── models/                  # schémas Pydantic (Garantie, Exclusion, Définition, verdicts…)
│   ├── llm/                     # LLMClient, adaptateurs, suivi des coûts
│   ├── ingestion/               # téléchargement, parsing, extraction, rattachement, vérification, batch
│   ├── pipeline/                # planification, candidates, évaluation, agrégation, citations, composition
│   ├── cp/                      # formulaire de CP, import, masquage des données personnelles
│   └── guards/                  # plafonds, cache
├── data/
│   ├── manifest.yaml            # corpus : sources, empreintes, éditions
│   ├── taxonomy.yaml
│   ├── raw/                     # PDF téléchargés (ignoré par git)
│   ├── contracts/               # données extraites, une entrée par (assureur, produit, édition)
│   └── examples/                # CP fictives, résultats pré-calculés
├── eval/
│   ├── cases/                   # cas annotés
│   └── results.json             # produit par le script d'évaluation
├── scripts/                     # points d'entrée en ligne de commande (téléchargement, ingestion, éval)
├── site/                        # site public GitHub Pages (données copiées par la CI)
├── docs/
│   ├── README.md                # index : fonctionnalité → fichier, liste des ADR
│   ├── strategie.md             # document de référence
│   ├── features/                # comment et pourquoi, par fonctionnalité
│   ├── adr/                     # décisions
│   └── phases/                  # phaseN.md (attendus), phaseN-plan.md (plan de l'agent)
├── tests/
└── .github/workflows/           # CI, déploiement du site
```

## Commandes

À compléter dès qu'elles existent (installation, lancement de l'app, tests, ingestion, évaluation).

```bash
uv sync --all-groups                                  # installation (dev + ingestion)
uv run streamlit run app/streamlit_app.py             # app en local
uv run pytest -q; uv run ruff check .; uv run ruff format --check .   # tests et lint (comme la CI)
uv run python scripts/download_corpus.py [--check]    # reconstruit / vérifie data/raw/ depuis le manifeste
# après toute modification de dépendance :
uv lock && uv export --format requirements-txt --no-dev --no-emit-project --locked -o app/requirements.txt
```

## Méthode de travail

- Le projet avance par phases (`docs/phases/`). Au début d'une phase : lire `phaseN.md`, rédiger
  `phaseN-plan.md`, le faire valider par l'utilisateur avant de coder.
- Travailler par petits incréments vérifiables ; lancer les tests avant chaque commit.
- Relancer l'évaluation (avec accord si elle coûte) après toute modification du pipeline ou des prompts.
- En cas de doute sur un choix structurant : proposer des options à l'utilisateur, puis écrire l'ADR.
