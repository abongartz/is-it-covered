# Extraction structurée des contrats

> Page en cours : le schéma, les unités, les définitions du lexique et la comparaison des citations sont en
> place (phase 1, incrément 2) ; l'extraction par LLM, le rattachement et le rapport arrivent à l'incrément 3.

## Ce que ça fait

Transforme l'arbre de sections approuvé d'un contrat en éléments typés, chacun avec sa source : garanties
(avec leurs conditions), exclusions (déclencheurs et exceptions), conditions générales et définitions. Le
résultat sera `data/contracts/<doc>/extraction.json`, commité (ADR 0009).

## Comment

### Schéma (`isitcovered.models.extraction`)

| Type | Contenu |
| --- | --- |
| `Quote` | `block_ref` (`<section>#<n>`, `#0` = titre), texte du bloc source, page, coordonnées |
| `Source` | document, section, chemin des titres, citations (au moins une) |
| `Condition` | `kind` (`peril`, `asset`, `location`, `circumstance`, `obligation`, `cp_subscription`), reformulation courte, termes définis, source |
| `GeneralCondition` | condition valable pour toutes les garanties des types listés (Ethias art. 2 #1) |
| `Guarantee` | intitulé, section, `kind` (`base`, `optional`, `extension`), `cp_optional`, concepts (avec confiance), facettes biens et lieux, conditions, source |
| `Exclusion` | portée `general` ou `specific`, garanties visées (fixées par le code), déclencheurs cumulatifs, exceptions, source |
| `Definition` | terme, texte, origine (`lexicon` ou `inline`), source |
| `ContractExtraction` | le tout, avec empreinte du PDF, parseur, modèle, version des prompts, date |

`ContractExtraction` refuse les identifiants en double, une exclusion générale qui vise une garantie, une
exclusion spécifique sans garantie ou visant une garantie inconnue.

### Unités (`ingestion/units.py`, ADR 0008)

Le plan de découpage d'Ethias donne 28 unités (art. 1, art. 2, les 20 sous-articles de l'art. 3, art. 4 à 9).
Chaque unité contient son chemin de titres, les titres voisins, les blocs propres des niveaux supérieurs en
contexte, puis chaque bloc avec sa référence, et se rend en texte pour le LLM :

```
Emplacement : Chapitre III – Garanties optionnelles > Article 4 – Vol et vandalisme
Sections voisines : Article 5 – Pertes indirectes ; Article 6 – Protection Juridique

Texte de l'unité :
[art-4#0] (titre, p. 14) Vol et vandalisme
[art-4#1] (p. 14) Cette garantie est accordée uniquement si mention en est faite expressément … {italique : conditions particulières}
```

### Définitions du lexique (`ingestion/definitions.py`, ADR 0011)

Une `Definition` par section `term` (53 chez Ethias), sans LLM ; une citation par bloc.

### Comparaison des citations (`isitcovered/textmatch.py`, ADR 0010)

Comparaison après normalisation (NFKC, apostrophes, guillemets, tirets, casse, espaces supprimés), extrait
d'au moins 15 caractères sauf s'il couvre tout le texte source ; le texte retenu est celui du bloc source,
retrouvé par une table de correspondance des positions.

## Pourquoi

- **Champs calculés par le code** (identifiants, pages, coordonnées, garanties visées, concepts, condition de
  souscription aux CP) : le LLM ne produit que ce qu'il est seul à pouvoir produire, la lecture du texte.
- **Références de blocs plutôt que positions** : stables, lisibles sur le PDF annoté, indépendantes du LLM.

## Vérification

- `tests/test_units.py` : sur un arbre synthétique (plan, contexte, références, rendu) et sur Ethias (28
  unités, `#0` pour les sous-articles sans texte, subdivisions de 3.20, en-tête de l'art. 4, phrase de champ
  du chapitre IV en contexte, 53 définitions). Les tests sur Ethias utilisent `data/parsed/` ou, en CI, le PDF
  reparsé.
- `tests/test_textmatch.py` : tolérance typographique, texte source restitué, citations inventées ou trop
  courtes refusées.
- `tests/test_models.py` : cohérence de `ContractExtraction`.

## Limites connues

- Chapitres V et VI (obligations, indemnisation) hors périmètre en phase 1 ; montants des plafonds et
  franchises non extraits.

ADR liés : [0008](../adr/0008-unites-extraction.md), [0009](../adr/0009-stockage-extraction.md),
[0010](../adr/0010-verification-citations.md), [0011](../adr/0011-definitions.md),
[0012](../adr/0012-taxonomie-v1.md).
