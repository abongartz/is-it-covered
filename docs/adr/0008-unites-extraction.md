# 0008 – Unités d'extraction et portée des exclusions

Statut : acceptée · Date : 2026-10-29

## Contexte

L'extraction structurée (garanties, exclusions, conditions) se fait par LLM. Il faut découper le contrat en
morceaux assez grands pour garder le contexte (une exclusion se lit avec la garantie qu'elle vise, une
condition avec l'en-tête de son article) et assez petits pour que la sortie reste courte et les citations
fiables. Chez Ethias, la portée ne se déduit pas toujours de la position : l'article 2 pose des exclusions
générales, l'article 4.3 « Plafonds » contient des conditions de couverture, et le chapitre IV précise son
champ d'application en une phrase.

## Décision

- **Périmètre phase 1** : chapitres I à IV d'Ethias. Les chapitres V et VI (obligations, indemnisation) sont
  reportés ; le lexique (VII) est converti par le code (ADR 0011).
- **28 unités** : art. 1, art. 2, chacun des 20 sous-articles de l'art. 3 (une garantie de base chacun ; 3.20
  avec ses subdivisions A et B), art. 4 à 9 entiers. Le plan de découpage est déclaré par document
  (`UNIT_PLANS` dans `ingestion/units.py`) : chapitres retenus et articles découpés par sous-article.
- **Contenu d'une unité** : chemin des titres, titres des sections voisines, blocs propres des niveaux
  supérieurs en contexte (phrase de champ du chapitre IV, en-tête d'article), puis chaque bloc de l'unité avec
  sa référence `<section>#<n>` (n ≥ 1 dans l'ordre des blocs, comme sur le PDF annoté ; `#0` = titre de la
  section, citable quand un sous-article n'a pas de texte propre). Les références sont calculées sur l'arbre
  approuvé, sans toucher au parseur.
- **Portée** : le LLM type le contenu ; la **garantie visée** par une exclusion spécifique est fixée par le
  code (garanties extraites du même article) ; une portée « générale » doit être justifiée par une citation.

## Alternatives

- **Bloc par bloc** : perd le contexte (une puce d'exclusion sans sa phrase d'introduction).
- **Contrat entier en un appel** : sortie très longue, citations moins fiables, échec coûteux à rejouer.
- **Un appel par article pour l'art. 3** : 20 garanties dans une seule sortie, alors que chaque sous-article
  est autonome.

## Conséquences

- Un nouveau contrat demande un plan de découpage (quelques lignes), relu avec son arbre.
- Les blocs de contexte sont citables : une exclusion générale de l'art. 2 reste rattachée à sa source.
