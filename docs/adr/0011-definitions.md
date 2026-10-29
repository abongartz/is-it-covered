# 0011 – Définitions : lexique converti par le code, injection ciblée en ligne

Statut : acceptée · Date : 2026-10-29

## Contexte

Le sens des mots d'un contrat vient de ses définitions, propres à chaque contrat (jamais fusionnées). Chez
Ethias, le lexique (chapitre VII) est déjà découpé par le parseur en 53 sections `def-*`, et l'italique signale
les termes définis dans le texte. D'autres définitions figurent hors du lexique (« Par contenu, nous
entendons… », art. 1.3).

## Décision

- **Lexique → définitions par le code** (`ingestion/definitions.py`) : une `Definition` par section `term`,
  texte = ses blocs, une citation par bloc ; aucun appel LLM.
- **Définitions hors lexique** : extraites par le LLM avec leur source (`origin: inline`), vérifiées comme les
  autres citations.
- **Injection en ligne** : termes signalés par l'extraction (`defined_terms`), passages en italique des blocs
  cités rapprochés des termes du lexique, et définitions du même article.

## Alternatives

- **Tout extraire par LLM** : plus cher, et moins sûr pour des textes déjà découpés exactement.
- **Injecter tout le lexique** à chaque évaluation : prompt plus long, et des définitions sans rapport
  diluent l'attention du modèle.

## Conséquences

- Un contrat sans lexique structuré dépendra entièrement de l'extraction LLM pour ses définitions.
- Un terme employé sans italique ni signalement peut ne pas être injecté : limite à suivre dans l'évaluation.
