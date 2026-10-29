# 0009 – Stockage de l'extraction : JSON commité avec les extraits cités

Statut : acceptée · Date : 2026-10-29

## Contexte

L'app hébergée doit évaluer des sinistres et afficher les clauses citées, mais elle n'a ni le PDF (jamais
commité) ni PyMuPDF (hors ligne, AGPL). Le texte intégral des CG ne doit pas être republié (ADR 0003).

## Décision

- `data/contracts/<doc>/extraction.json` est **commité** : garanties, exclusions, conditions, définitions,
  chacune avec sa source (section, chemin des titres, et pour chaque citation : référence de bloc, **extrait
  exact**, page, coordonnées).
- Les citations sont **au niveau de la clause** : seuls les passages cités sont publiés, pas l'arbre complet.
- Les définitions du lexique sont reprises telles quelles (textes courts).
- Un lien vers la source officielle accompagne toute citation affichée.
- Validation par le schéma Pydantic `ContractExtraction` (identifiants uniques, exclusions spécifiques
  rattachées à des garanties existantes).

## Alternatives

- **Ne publier que des références** (bloc, positions) et retélécharger le PDF au démarrage de l'app : PyMuPDF
  en ligne (lourd, AGPL), ou un autre extracteur dont le texte diffère et casse les citations.
- **SQLite** : inutile pour quelques centaines d'éléments ; un JSON se relit dans un diff git.

## Conséquences

- Une partie du texte des CG est publiée (les clauses pertinentes et le lexique), avec attribution et lien ;
  à réexaminer si un assureur s'y oppose.
- Toute réextraction se voit dans le diff (ADR 0007).
