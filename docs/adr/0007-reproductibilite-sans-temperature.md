# 0007 – Reproductibilité sans température

Statut : acceptée · Date : 2026-10-29

## Contexte

`CLAUDE.md` imposait « température 0 pour l'ingestion ». Depuis le 2026-10-21, l'API Anthropic refuse
`temperature`, `top_p` et `top_k` (erreur 400) sur tous les modèles. De plus, une température nulle ne
garantissait déjà pas des sorties identiques.

## Décision

La reproductibilité de l'ingestion repose sur :

- une **version de modèle et un effort figés** par route (ADR 0006) ;
- des **sorties d'ingestion commitées**, avec le modèle, l'empreinte des prompts et la date ;
- une **réingestion explicite** (commande lancée volontairement), jamais implicite.

Aucun paramètre d'échantillonnage n'est envoyé (test sur la requête).

## Alternatives

Aucune : contrainte de l'API.

## Conséquences

- Deux passages d'extraction peuvent différer ; la référence est la sortie commitée, et toute différence se
  voit dans le diff git.
- La règle de `CLAUDE.md` est remplacée par celle-ci.
