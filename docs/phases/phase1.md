# Phase 1 – Chaîne complète sur un contrat

## But

Obtenir un premier verdict cité, de bout en bout, sur un seul contrat : extraction structurée hors ligne,
pipeline en ligne minimal, app utilisable et première version du site de documentation.
À la fin de cette phase, le projet est démontrable.

## Attendus

4. **Couche LLM**
   - Une interface unique pour obtenir des sorties structurées (Pydantic) d'un LLM, indépendante du fournisseur.
   - Un premier fournisseur branché ; changement de fournisseur ou de modèle par configuration.
   - Chaque appel enregistre tokens et coût estimé.

5. **Schéma et taxonomie v1**
   - Modèles de données pour : source (document, page, chemin de sections, texte exact, coordonnées),
     garantie (avec ses conditions, concepts, biens, lieux, caractère optionnel selon les CP),
     exclusion (portée générale ou spécifique, exceptions), définition.
   - `data/taxonomy.yaml` : une quinzaine de concepts sur l'axe des périls, facettes séparées (biens, lieux,
     statut), chaque concept avec description, exemples et notes « inclut / n'inclut pas ».

6. **Extraction du premier contrat**
   - Garanties, exclusions et définitions extraites du contrat de la phase 0, chacune avec sa source.
   - Chaque garantie rattachée à un ou plusieurs concepts avec un score de confiance ; les garanties non
     rattachées sont classées « autre ».
   - Chaque texte cité est vérifié contre le document ; les citations introuvables sont signalées.
   - Un rapport d'ingestion liste garanties non rattachées et citations invalides.
   - Exécution en synchrone, sur ce seul contrat.

7. **Pipeline en ligne minimal** (une seule question de couverture, pas encore de découpage de message)
   - Analyse du sinistre en faits typés.
   - Sélection des garanties candidates par les concepts.
   - Évaluation de chaque condition et exclusion candidate : remplie, non remplie, inconnue ou ambiguë,
     avec la clause citée ; définitions du contrat injectées.
   - Agrégation déterministe en code : couvert, non couvert ou indéterminé, avec faits manquants.
   - Vérification des citations avant restitution.

8. **App v1**
   - Choix du contrat, saisie d'un sinistre, affichage du verdict, du raisonnement condition par condition
     et des clauses citées avec leur page.
   - Déployée à l'URL publique.

9. **Documentation v1**
   - Site public sur GitHub Pages : le problème, l'architecture (schéma), les choix principaux.
   - Déploiement automatique du site à chaque push sur `main`.
   - `docs/features/` à jour pour chaque brique livrée ; ADR pour chaque choix (fournisseur, modèle, format
     de stockage, etc.).

## Critères de fin de phase

- Les deux exemples de l'énoncé (vélo dans le local commun ouvert, bougie sur la table de jardin) obtiennent
  chacun un verdict justifié, ou un « indéterminé » qui nomme ce qui manque, avec des citations vérifiées.
- Ce résultat est reproductible depuis l'app en ligne.
- Le site public est en ligne et décrit l'architecture effectivement implémentée.
- Coût LLM cumulé du projet connu et affiché dans le plan de phase.

## Hors périmètre

Découpage des messages composés, CP, plafonds de coût, autres contrats, évaluation chiffrée.

---

# Plan d'action

Statut : **en cours (incrément 2)** · Coût LLM cumulé du projet : **0,00003 $** (phase 0 : 0 €) · Enveloppe : **6 €** (clé plafonnée à 5 $)

Le plan découpe la phase en 6 incréments. Chacun se termine par des tests verts, une PR fusionnée dans `main`
(squash, CI verte) et une app déployée qui fonctionne. La CI n'appelle jamais de LLM : les tests utilisent
un client simulé et des réponses enregistrées.

## Contexte utile (constaté sur le contrat Ethias)

- Arbre approuvé (ADR 0004) : `data/parsed/be-ethias-habitation-2025-03/sections.json` (local, régénéré par
  `scripts/parse_contract.py` ; en CI, les tests le reconstruisent à partir du PDF téléchargé). 7 chapitres,
  21 articles, 83 sous-articles, 19 intitulés ou subdivisions, 53 termes au lexique (une section `def-*` par
  terme). Chapitre I : personnes et biens assurés (art. 1, dont des définitions : « Par contenu, nous
  entendons… », art. 1.3 #6) ; II : objet de l'assurance (art. 2) et garanties de base (art. 3) ;
  III : garanties optionnelles (art. 4 à 6) ; IV : extensions (art. 7 à 9) ; V et VI : obligations,
  indemnisation, dispositions administratives ; VII : lexique.
- L'article 2 n'est pas une garantie : il pose une **condition générale** (#1 : dégâts matériels « causés
  accidentellement aux biens assurés par un événement relevant d'une garantie couverte »), les **exclusions
  générales** (#6 à #16, valables pour les garanties de base et optionnelles) et la **dépendance des
  extensions** (#17 : le chapitre IV ne s'applique que « dans le cadre d'un sinistre couvert »). La portée ne se
  déduit donc pas seulement de la position dans l'arbre.
- Sous-articles **sans texte propre** : 3.1 à 3.4 (incendie, combustion sans flamme, explosion, fumée et
  suie), 3.8 (foudre), 3.10 (décongélation) ; 3.20 n'a de texte que dans ses subdivisions A et B. Leur sens
  vient du lexique (« Incendie », « Explosion ou implosion », « Décongélation ») ou n'est pas défini
  (« combustion sans flamme », « foudre »). « Effraction », déterminant pour le vélo, n'est pas au lexique.
- Le sous-article 4.3 « Plafonds d'intervention » contient aussi des **conditions de couverture** (#6, #7 :
  caves ou garages « complètement fermés », occupation partielle du bâtiment).
- Le texte mélange apostrophes typographiques et droites, et garde des artefacts de coupure (« et/ ou »).
- Les articles 4 à 6 commencent par « Cette garantie est accordée uniquement si mention en est faite
  expressément… dans les conditions particulières » : bloc de l'article, avant ses sous-articles.
- Des définitions figurent hors du lexique (« Par contenu, nous entendons… », art. 1.3).
- Les listes imbriquées sont aplaties (l'imbrication ne se voit que dans l'abscisse du bloc) ; les blocs n'ont
  pas d'identifiant stocké.
- **Aucune modification du parseur n'est prévue** : elle invaliderait l'approbation (ADR 0004).

## Décisions à valider

| # | Sujet | Proposition | Alternatives | ADR |
| --- | --- | --- | --- | --- |
| D1 | Fournisseur et SDK | **Anthropic**, SDK officiel `anthropic` (sorties structurées natives `client.messages.parse(..., output_format=ModèlePydantic)`), derrière le protocole `LLMClient` ; une seule nouvelle dépendance | **Instructor** (prévu par la stratégie) : multi-fournisseur immédiat, mais dépendances supplémentaires (surface d'attaque, cf. LiteLLM) et inutile tant qu'il n'y a qu'un fournisseur ; un 2ᵉ adaptateur s'écrira derrière le même protocole | 0005 |
| D2 | Modèles | Ingestion : **`claude-sonnet-5-5`** (2 $ / 10 $ par M tokens), effort `high`. En ligne (faits, évaluation) : **`claude-haiku-5-5`** (0,10 $ / 0,50 $), effort `medium` ; repli sur Sonnet 5.5 par configuration si les exemples échouent à cause du modèle. Identifiants exacts, jamais d'alias | Opus 5.5 pour l'ingestion (4 $ / 20 $ : 2× plus cher) ; Haiku pour tout (moins fiable à l'extraction, dont les erreurs se propagent) | 0006 |
| D3 | Reproductibilité | L'API refuse désormais `temperature` (400 depuis le 2026-10-21) : la règle « température 0 pour l'ingestion » de `CLAUDE.md` devient « version de modèle et effort figés ; sorties d'ingestion commitées avec modèle, version des prompts et date ; une réingestion est explicite » | Aucune (contrainte de l'API) | 0007 |
| D4 | Unités d'extraction et portée | **Chapitres I à IV seulement**, en **28 unités** : art. 1, art. 2, chacun des 20 sous-articles de l'art. 3 (3.20 avec ses subdivisions), art. 4 à 9 entiers. Chaque unité contient le chemin des titres, le bloc d'en-tête de l'article, les titres des sections voisines et les blocs numérotés (`art-4.4#3` ; `#0` = titre de la section, citable pour les sous-articles sans texte). Le LLM type le contenu ; la **garantie visée** par une exclusion spécifique est fixée par le code (garanties extraites du même article) ; une portée « générale » doit être justifiée par une citation. Chapitres V et VI hors périmètre en phase 1 (obligations, indemnisation) | Extraction bloc par bloc (perd le contexte) ; contrat entier en un appel (sortie trop longue, citations moins fiables) | 0008 |
| D5 | Stockage et publication | `data/contracts/<doc>/extraction.json` **commité**, avec les extraits exacts (citations au niveau de la clause, pas l'arbre complet). Indispensable à l'app déployée, qui n'a ni le PDF ni PyMuPDF. Les définitions du lexique sont reprises telles quelles (courtes). Lien vers la source officielle partout | Ne publier que des références (bloc, positions) et retélécharger le PDF au démarrage de l'app : PyMuPDF (AGPL, lourd) en ligne, ou un autre extracteur dont le texte diffère et casse les citations | 0009 |
| D6 | Vérification des citations | **Deux niveaux** : hors ligne, chaque extrait doit se retrouver dans le bloc cité de `sections.json` ; en ligne, chaque citation de l'évaluateur doit se retrouver dans un extrait vérifié de la clause citée. Comparaison après normalisation : Unicode NFKC, apostrophes (’ ‘ ʼ → '), guillemets (« » “ ” → "), tirets (– — ‑ → -), casse ignorée, **tous les espaces supprimés** (absorbe « et/ ou »). Extrait d'au moins 15 caractères, sauf s'il couvre tout le bloc ou tout le titre (`#0` : « L'incendie », « La foudre »). Le texte conservé et affiché est **le passage correspondant du bloc source** (retrouvé grâce à une table de correspondance entre positions normalisées et positions d'origine), jamais celui du LLM. Une citation invalide en ligne fait passer le jugement concerné à `inconnue` | Vérification en ligne contre le PDF (impossible sans le PDF, cf. D5) ; égalité stricte (faux rejets dus aux apostrophes) | 0010 |
| D7 | Définitions | Lexique converti **par le code** (une `Definition` par section `def-*`, aucun appel LLM) ; définitions hors lexique (« Par contenu, nous entendons… ») extraites par le LLM avec leur source. Injection en ligne : termes signalés par l'extraction + passages en italique des blocs cités rapprochés des termes du lexique + définitions du même article | Tout extraire par LLM (plus cher, moins sûr pour des textes déjà découpés) | 0011 |
| D8 | Taxonomie v1 | 15 concepts de périls (liste de la stratégie) + `autre` ; facettes biens, lieux, statut. Rattachement par un appel LLM séparé (taxonomie + garanties extraites → concepts avec confiance 0–1) ; seuil 0,5, sinon `autre` | Rattachement dans l'appel d'extraction (prompt plus long, taxonomie répétée à chaque article) | 0012 |
| D9 | Agrégation | Logique à trois valeurs (détails ci-dessous) ; « aucune garantie candidate » ⇒ `indéterminé` | — | 0013 |
| D10 | Garde-fou minimal en ligne | L'app publique utilise notre clé dès la phase 1 alors que les plafonds sont en phase 2 : **plafond global journalier en coût estimé (1 € / jour, compteur en mémoire du processus) et 10 analyses par session**, saisie limitée à 1 000 caractères, `max_tokens` fixé. Les exemples (vélo, bougie) s'affichent depuis des traces pré-calculées, sans appel | Attendre la phase 2 (risque de consommer le budget) ; app sans analyse en direct (ne remplit pas « reproductible depuis l'app ») | 0014 |
| D11 | Site | Page statique `site/index.html` (HTML, Tailwind et Mermaid par CDN, versions figées), données lues dans `site/data/*.json` copiés par la CI depuis `data/` ; déploiement GitHub Pages par GitHub Actions (actions épinglées par SHA) | Quarto (plus simple, moins libre visuellement) ; MkDocs | 0015 |

## Spécifications

### Schéma (`src/isitcovered/models/extraction.py`)

Identifiants et champs en anglais (règle de `CLAUDE.md`) ; la stratégie les nommait en français.

- `Quote` : `block_ref` (`<section_id>#<n>`, n à partir de 1 dans l'ordre des blocs de la section, comme dans
  le PDF annoté ; `#0` = titre de la section), `text` (texte du bloc source correspondant, cf. D6), `page`,
  `bbox` (du bloc ou du titre). Les références sont calculées à partir de l'arbre, sans modifier le parseur.
- `Source` : `doc_id`, `section_id`, `section_path` (titres du chapitre à la section), `quotes: list[Quote]`.
- `Condition` : `id`, `kind` (`peril`, `asset`, `location`, `circumstance`, `obligation`, `cp_subscription`),
  `text` (reformulation courte), `defined_terms`, `source`.
- `Guarantee` : `id` (`<doc>/g/<slug>`), `name` (intitulé du contrat), `section_id`, `kind` (`base` |
  `optional` | `extension`), `cp_optional` (vrai si le contrat exige une mention aux CP ; fixé par le LLM avec
  la citation correspondante, par exemple le bloc d'en-tête de l'art. 4), `concepts: list[ConceptLink]`
  (concept, confiance ; rempli par le rattachement), `assets`, `locations` (facettes), `conditions`, `source`.
  Pour une garantie `cp_optional`, le **code** ajoute une condition `cp_subscription` (« la garantie figure aux
  CP »), évaluée comme les autres à partir des faits : sans information dans le message, elle est `unknown`.
- `Exclusion` : `id`, `scope` (`general` | `specific`), `guarantee_ids` (rempli par le code pour `specific`),
  `triggers: list[Condition]` (cumulatives : toutes doivent être remplies), `exceptions: list[Condition]`,
  `defined_terms`, `source`. Une clause qui énumère des cas alternatifs donne une exclusion par cas.
- `GeneralCondition` : condition valable pour toutes les garanties (art. 2 #1 chez Ethias), ajoutée par le
  code aux conditions de chaque garantie candidate.
- `Definition` : `term`, `text`, `origin` (`lexicon` | `inline`), `source`.
- `ContractExtraction` : `doc_id`, `source_sha256`, `parser`, `model`, `prompt_version` (empreinte des
  fichiers de prompt), `created_at`, `general_conditions`, `guarantees`, `exclusions`, `definitions`.

Le LLM ne produit que des schémas de sortie dédiés (`ExtractionUnitOutput`…) sans les champs calculés par le
code (identifiants, pages, coordonnées, garanties visées, concepts, condition `cp_subscription`). Les montants
des plafonds et franchises ne sont pas extraits en phase 1 ; une **condition de couverture** placée dans un
sous-article de plafonds (art. 4.3 #6, #7) est extraite comme condition ou exclusion.

### Agrégation (`src/isitcovered/pipeline/aggregate.py`)

- Valeurs : `met` = vrai, `not_met` = faux, `unknown` et `ambiguous` = inconnu (logique de Kleene).
- Exclusion applicable = ET(déclencheurs) ET NON (OU des exceptions).
- Résultat d'une garantie de base ou optionnelle = ET(conditions générales, conditions propres, condition
  `cp_subscription` le cas échéant) ET NON (OU des exclusions applicables : générales + spécifiques).
- Résultat d'une **extension** = (résultat propre, calculé comme ci-dessus) ET (OU des résultats des garanties
  de base ou optionnelles candidates) : une extension ne rend jamais à elle seule un sinistre couvert.
- Verdict = OU sur les garanties candidates : une garantie vraie ⇒ `couvert` ; toutes fausses ⇒ `non couvert`
  (chacune justifiée par une condition non remplie ou une exclusion applicable, citées) ; sinon `indéterminé`,
  avec les faits manquants (conditions `unknown`) et les clauses ambiguës des garanties restées inconnues.
- Aucune garantie candidate ⇒ `indéterminé` (« aucune garantie trouvée »), jamais `non couvert`.
- Testé exhaustivement (tables de vérité) sans LLM.

### Pipeline en ligne (`src/isitcovered/pipeline/`)

1. **Faits** (1 appel) : description de l'événement, cause, biens endommagés, lieu, statut de l'assuré,
   circonstances (liste), faits explicitement inconnus ; concepts de périls activés (plusieurs possibles :
   rappel) avec confiance.
2. **Candidates** (code) : garanties dont un concept est activé ; exclusions générales + spécifiques de ces
   garanties ; définitions à injecter (D7).
3. **Évaluation** (1 appel par garantie candidate) : pour chaque condition, déclencheur et exception :
   statut, justification courte, citation (clause + extrait), fait manquant le cas échéant.
4. **Agrégation** (code), puis **vérification des citations** (D6).
5. **Trace** (`pipeline/trace.py`) : faits, candidates, jugements, verdict, citations vérifiées, modèles,
   tokens et coût ; sérialisée en JSON pour l'app, le site et les tests.

### Couche LLM (`src/isitcovered/llm/`)

- `LLMClient` (protocole) : `structured(system, messages, schema, *, max_tokens, route) -> LLMResult[T]`
  (sortie validée + usage) et `count_tokens(system, messages, schema, *, route) -> int` (gratuit, pour les
  estimations). L'adaptateur Anthropic est le seul fichier qui importe `anthropic`.
- Routes (`ingestion`, `linking`, `facts`, `evaluation`) → modèle et effort dans `llm/config.py`, surchargeables
  par `ISITCOVERED_MODEL_<ROUTE>` (format `fournisseur/modèle`) et `ISITCOVERED_EFFORT_<ROUTE>`.
- Tarifs dans `llm/pricing.py` (USD par M tokens : entrée, sortie, lecture et écriture de cache ; paliers
  selon la taille du prompt, par exemple Haiku 5.5 au-delà de 100 k tokens) ; coût estimé par appel.
- **Journal des coûts** `data/costs/ledger.jsonl` (commité : date, route, modèle, tokens, coût ; jamais de
  contenu ni de clé) : alimenté par les scripts hors ligne (`extract_contract.py`, `ask.py`, appel de fumée).
  Les tests et le client simulé n'y écrivent jamais (chemin injecté, absent par défaut). L'app en ligne
  n'écrit pas sur disque : compteurs de session et de processus (D10). Coût cumulé du projet = somme du
  journal + analyses en direct faites pendant la phase (coût affiché par l'app, reporté au journal du plan).
- **Clé** : jamais sur disque. Sur l'hébergeur : `st.secrets["ANTHROPIC_API_KEY"]`. En local (scripts et app) :
  variable d'environnement **`ISITCOVERED_ANTHROPIC_API_KEY`** (et non `ANTHROPIC_API_KEY`, que Claude Code
  lirait pour son propre usage), lue par `llm/` et passée explicitement au client. Aucun `secrets.toml` local :
  l'app lit d'abord la variable d'environnement et n'accède à `st.secrets` que si elle est absente (sans
  fichier de secrets, `st.secrets` lève une erreur en local).
  Journaux des bibliothèques `anthropic` et `httpx2` au niveau `WARNING` ; erreurs traduites sans détail.
- Points d'API à respecter : `max_tokens` toujours fixé ; pas de `temperature` ; vérifier `stop_reason`
  (`refusal`, `max_tokens`) avant de lire la sortie ; cache de prompt sur les instructions et la taxonomie
  (préfixe minimal selon le modèle : un prompt court n'est pas mis en cache) ; pas de repli automatique en cas
  de refus sur Haiku 5.5 (le refus devient une erreur explicite).
- Client simulé (`llm/fake.py`) qui rejoue des sorties enregistrées : tous les tests passent sans réseau.
- Prompts versionnés dans `src/isitcovered/prompts/*.md` (en français, comme les contrats).

## Incréments

### Incrément 1 – Couche LLM et suivi des coûts

1. Dépendance `anthropic` (version exacte), `uv lock`, export de `app/requirements.txt`.
2. `llm/` : protocole, adaptateur Anthropic, configuration des routes, tarifs, journal des coûts, client simulé.
3. `CLAUDE.md` : règle de reproductibilité (D3) ; règle des clés complétée (en local, variable
   `ISITCOVERED_ANTHROPIC_API_KEY`) ; arborescence (`prompts/`, `data/costs/`) ; commandes.
4. Tests : calcul de coût, routage par configuration, journal, client simulé, absence de clé dans les messages
   d'erreur ; un test vérifie qu'aucun module hors `llm/` (et du futur batch d'ingestion) n'importe `anthropic`.
5. Appel de fumée réel unique (Haiku, < 0,01 €) pour valider la clé et l'enregistrement du coût.
6. ADR 0005, 0006, 0007 ; `docs/features/llm.md` ; `.streamlit/secrets.toml.example` vérifié (secret de
   l'hébergeur seulement).

### Incrément 2 – Schéma et taxonomie v1

1. `models/extraction.py`, `models/taxonomy.py`, `models/facts.py`, `models/verdict.py`.
2. `data/taxonomy.yaml` (D8), validé par Pydantic : identifiants stables, libellé, description, exemples,
   `includes`, `excludes`.
3. `ingestion/units.py` : unités d'extraction depuis l'arbre (D4), références de blocs ; `ingestion/definitions.py`
   (lexique → définitions, D7).
4. Tests : 28 unités d'Ethias (chemins, en-têtes d'article inclus, `#0` pour les sous-articles sans texte,
   découpage de l'art. 3), 53 définitions du lexique, normalisation des citations (D6), taxonomie valide (une
   quinzaine de concepts + `autre`, identifiants uniques).
5. ADR 0008 à 0012 ; `docs/features/extraction.md` (début), `docs/features/taxonomie.md`.

### Incrément 3 – Extraction du contrat Ethias

1. `ingestion/extract.py`, `ingestion/link.py`, `ingestion/verify.py`, `ingestion/report.py` ;
   `scripts/extract_contract.py [DOC_ID] [--units art-4,art-3.1] [--dry-run]`.
2. `--dry-run` : comptage des tokens (`count_tokens`, gratuit) et coût estimé, affichés **avant** tout appel.
3. Mise au point synchrone sur **art. 4 et art. 3.1–3.5** (vol, incendie, dégât des eaux), puis passage complet.
4. Sorties : `data/contracts/<doc>/extraction.json` et `ingestion_report.json` (garanties non rattachées,
   citations invalides, unités en échec) ; rapport lisible affiché par le script.
5. Tests sans réseau : vérification des citations (exactes, normalisées, introuvables), portée des
   exclusions fixée par le code, rapport ; cohérence de l'extraction commitée (identifiants uniques, toute
   exclusion spécifique vise une garantie existante, chaque extrait présent dans son bloc : le test reparse le
   PDF quand il est disponible, comme `tests/test_contract_structure.py`, sinon il est ignoré).
6. `docs/features/extraction.md` complété (méthode, chiffres du passage, limites).

Vérification : toutes les citations vérifiées ou signalées ; garanties attendues présentes (incendie,
combustion sans flamme, explosion, fumée et suie, dégât des eaux, vol et vandalisme…), chacune rattachée ou
classée `autre`.

### Incrément 4 – Pipeline en ligne en ligne de commande

1. `pipeline/facts.py`, `candidates.py`, `evaluate.py`, `aggregate.py`, `citations.py`, `trace.py`, `run.py` ;
   `scripts/ask.py --doc <id> "<sinistre>" [--out trace.json]`.
2. Tests : agrégation exhaustive, candidates et définitions injectées sur l'extraction commitée, vérification
   des citations en ligne, pipeline complet avec le client simulé.
3. Exécution réelle des deux exemples ; traces commitées dans `data/examples/<doc>/velo.json` et
   `bougie.json` (date, modèles, et commit du code qui a produit la trace : `HEAD` au moment de l'exécution,
   avec la mention `dirty` si l'arbre de travail est modifié).
4. ADR 0013 ; `docs/features/pipeline.md`.

Hypothèses à confirmer par l'utilisateur sur les traces (pas une cible imposée au pipeline) :

- **Vélo** : garantie vol optionnelle (souscription aux CP inconnue) et exclusion 4.4 « biens se trouvant dans
  les parties communes… » ⇒ `non couvert` en citant 4.4 si l'exclusion est jugée applicable, sinon
  `indéterminé` nommant l'option vol et les faits manquants (effraction, fermeture, occupation partielle).
- **Bougie** : la définition d'« incendie » exige des flammes et un embrasement susceptible de se propager ;
  « combustion sans flamme » (3.2) n'est pas définie ⇒ attendu `indéterminé` (clause ambiguë, cause de la
  fonte), ou `non couvert` seulement si toutes les garanties candidates sont écartées par une clause citée.

### Incrément 5 – App v1

1. Page « Analyser un sinistre » : choix du contrat, saisie (1 000 caractères max), boutons d'exemple
   (traces pré-calculées, sans appel), analyse en direct avec `st.status`.
2. Affichage : verdict, faits retenus, par garantie candidate les conditions et exclusions (statut,
   justification, citation avec page), faits manquants, définitions utilisées, coût de la requête.
3. Garde-fou minimal (D10) dans `guards/` ; notice : ne pas saisir de données personnelles.
4. Tests `AppTest` avec le client simulé (aucun appel réel en CI), plafond déclenché, exemples affichés.
5. ADR 0014 ; `docs/features/app.md`. Vérification sur l'URL publique : un exemple en direct, avec les outils
   Chrome si la session en dispose (une app Streamlit ne se teste pas avec `curl`), sinon à demander à
   l'utilisateur ; résultat et coût consignés au journal de ce plan.

### Incrément 6 – Site v1 et clôture

1. `site/index.html` : le problème, pourquoi l'approche naïve échoue, architecture **effectivement
   implémentée** (schéma Mermaid), modèle de données et agrégation, choix principaux (liens vers les ADR),
   pas à pas des deux exemples lus depuis les traces, coûts lus depuis le journal ; chaque bloc chiffré avec
   date, commit et modèle.
2. `scripts/build_site_data.py` (copie et conversion des JSON vers `site/data/`, dossier ignoré par git,
   produit par la CI ou en local pour prévisualiser) ; workflow `.github/workflows/pages.yml` (actions
   épinglées par SHA) ; GitHub Pages en mode « GitHub Actions ».
3. Schéma d'architecture de `docs/strategie.md` (ligne 82, non exporté) remplacé par le même schéma Mermaid.
4. `README.md` (lien vers le site), `docs/README.md` (index), `CLAUDE.md` (commandes, arborescence).
5. ADR 0015 ; critères de fin vérifiés ; coût cumulé reporté dans ce plan ; statut « terminé ».

## Notes pratiques

- **Déploiement de l'app** : Streamlit Community Cloud redéploie `main` automatiquement
  (https://is-it-covered.streamlit.app/, Python 3.12, dépendances lues dans `app/requirements.txt`) ; les
  secrets se règlent dans les paramètres de l'app sur share.streamlit.io (action de l'utilisateur).
- **SHA des actions GitHub** : `gh api repos/<owner>/<action>/git/ref/tags/<tag>` (si l'objet est un tag
  annoté, suivre `object.url` jusqu'au commit) ; format d'épinglage : `.github/workflows/ci.yml`.
- **Activer Pages** (si autorisé) : `gh api -X POST repos/abongartz/is-it-covered/pages -f build_type=workflow`.
- **Windows** : la sortie redirigée est en cp1252 ; lancer les scripts avec `uv run python -X utf8 …` ou
  `PYTHONUTF8=1` ; écrire les fichiers avec `encoding="utf-8", newline="\n"` (`.gitattributes` impose LF) ;
  préférer les outils d'édition de fichiers aux heredocs pour les contenus avec guillemets.
- **PDF annoté** : `data/parsed/<doc>/annotated.pdf` montre les identifiants de blocs (`art-4.4 #3`) utilisés
  par les citations.

## Budget LLM

| Poste | Estimation | Pré-autorisé par la validation du plan |
| --- | --- | --- |
| Fumée (incrément 1) | < 0,01 € | oui |
| Mise au point de l'extraction (art. 4, 3.1–3.5, quelques itérations) | ~0,50 € | oui |
| Passage complet d'extraction + rattachement (28 unités, ~130 k tokens en entrée, ~100 k en sortie avec réflexion, Sonnet 5.5) | ~1,30 € par passage, 2 passages au plus | oui, si le `--dry-run` annonce ≤ 1,50 € par passage |
| Mise au point du pipeline en ligne (Haiku 5.5, ~0,01 € par question, ~100 questions) | ~1 € | oui |
| Essais de l'évaluation avec Sonnet 5.5 si Haiku ne suffit pas (~0,05 € par question) | ~1 € | oui |
| **Total phase 1** | **~5 €** | **enveloppe de 6 €** |

Règles pour l'agent : afficher l'estimation avant chaque appel ou série d'appels ; s'arrêter et demander si
une étape dépasse son estimation de plus de 50 %, si le cumul de la phase atteint 6 €, ou avant toute dépense
non listée. Le cumul (journal `data/costs/ledger.jsonl`) est reporté dans l'en-tête de ce plan à chaque
incrément. Tarifs relevés le 2026-10-29 ; USD comptés 1:1 en euros par prudence.

## Actions attendues de l'utilisateur

1. Valider ce plan, les décisions D1 à D11 et l'enveloppe de 6 €.
2. Avant l'incrément 1 : créer une clé API Anthropic dédiée avec une **limite de dépense** réglée dans la
   console (10 $ par exemple), puis la rendre disponible à la session : variable d'environnement
   **`ISITCOVERED_ANTHROPIC_API_KEY`** définie avant de lancer Claude Code (jamais écrite dans le dépôt ; ne
   pas utiliser `ANTHROPIC_API_KEY`, que Claude Code lirait pour son propre usage).
3. Incrément 5 : ajouter `ANTHROPIC_API_KEY` dans les secrets de l'app sur Streamlit Community Cloud.
4. Incrément 6 : autoriser l'agent à activer GitHub Pages (`gh api`, source « GitHub Actions »), ou le faire
   dans les réglages du dépôt.
5. Fin de phase : relire les deux traces (vélo, bougie) et valider les verdicts.

## Risques

| Risque | Parade |
| --- | --- |
| Extraction incomplète ou fausse (erreur propagée à toutes les questions) | Modèle fort, citations vérifiées, rapport d'ingestion, mise au point sur les articles des deux exemples avant le passage complet |
| Garantie candidate manquée (rattachement aux concepts) | Plusieurs concepts activés par sinistre (rappel), seuil bas, garanties `autre` listées au rapport |
| Haiku trop faible pour l'évaluation | Route `evaluation` configurable ; essai Sonnet 5.5 dans l'enveloppe |
| Budget consommé par l'app publique | Garde-fou minimal (D10), limite de dépense côté fournisseur, exemples pré-calculés |
| Republication du texte des CG | Seuls les extraits de clauses et le lexique sont publiés, avec lien vers la source (D5) |
| Évolution de l'API (paramètres refusés, modèles retirés) | Identifiants exacts, adaptateur unique, test de fumée |

## Critères de fin de phase → preuve

| Critère | Preuve |
| --- | --- |
| Vélo et bougie : verdict justifié ou `indéterminé` argumenté, citations vérifiées | `data/examples/<doc>/velo.json`, `bougie.json` ; validation de l'utilisateur |
| Reproductible depuis l'app en ligne | Analyse en direct sur l'URL publique, consignée au journal de ce plan |
| Site public décrivant l'architecture implémentée | URL GitHub Pages, workflow vert |
| Coût cumulé connu et affiché | En-tête de ce plan, `data/costs/ledger.jsonl`, site |

## Journal

- 2026-10-29 : plan rédigé (phase 0 terminée : contrat Ethias parsé et approuvé, ADR 0001 à 0004).
- 2026-10-29 : plan audité par une session neuve (lecture seule) ; corrections : nom de la variable de clé,
  unités d'extraction listées, conditions générales et extensions, CP, déclencheurs multiples, normalisation
  des citations, périmètre du journal des coûts, notes pratiques, décomptes Ethias (53 termes, 83 sous-articles).
- 2026-10-29 : plan validé par l'utilisateur (décisions D1 à D11). Clé API dédiée créditée de 5 $, sans
  rechargement automatique : c'est le plafond effectif (l'enveloppe de 6 € ne sera pas atteinte). Consigne :
  s'arrêter et décrire précisément chaque appel API avant de le lancer.
- 2026-10-29 : incrément 1 codé (SDK `anthropic` 2.3.0, `llm/`, tests sans réseau, ADR 0005 à 0007).
- 2026-10-29 : appel de fumée (Haiku 5.5, route `facts`) : comptage gratuit 269 tokens, puis un appel réel
  269 tokens en entrée, 12 en sortie, 0,000033 $ ; inscrit au journal `data/costs/ledger.jsonl`.
- 2026-10-29 : incrément 1 fusionné (#7). Incrément 2 : modèles (extraction, taxonomie, faits, verdict),
  taxonomie v1 (15 concepts + `other`), 28 unités et 53 définitions d'Ethias, comparaison des citations
  (`textmatch.py`), ADR 0008 à 0012 ; aucun appel LLM.
