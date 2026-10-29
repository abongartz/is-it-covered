# 0006 – Modèles : Sonnet 5.5 hors ligne, Haiku 5.5 en ligne

Statut : acceptée · Date : 2026-10-29

## Contexte

Budget LLM total de 20 €. L'extraction hors ligne est faite une fois par contrat et ses erreurs se propagent à
toutes les questions ; l'analyse en ligne est répétée à chaque question et doit rester bon marché.

## Décision

| Route | Usage | Modèle | Effort |
| --- | --- | --- | --- |
| `ingestion` | extraction des garanties, exclusions, définitions | `claude-sonnet-5-5` (2 $ / 10 $ par M tokens) | `high` |
| `linking` | rattachement aux concepts de la taxonomie | `claude-sonnet-5-5` | `high` |
| `facts` | analyse du sinistre en faits typés | `claude-haiku-5-5` (0,10 $ / 0,50 $ ; 0,50 $ / 2,50 $ au-delà de 100 k tokens de prompt) | `medium` |
| `evaluation` | jugement des conditions d'une garantie | `claude-haiku-5-5` | `medium` |

- Identifiants exacts, **jamais d'alias** (`latest` refusé par la configuration).
- Repli de l'évaluation sur Sonnet 5.5 par configuration (`ISITCOVERED_MODEL_EVALUATION`) si Haiku échoue sur
  les exemples à cause du modèle.
- Réflexion adaptative laissée active (comportement par défaut de ces modèles) ; la profondeur se règle par
  l'effort.

## Alternatives

- **Opus 5.5 pour l'ingestion** (4 $ / 20 $) : deux fois plus cher, sans nécessité démontrée.
- **Haiku pour tout** : moins fiable à l'extraction, dont les erreurs se propagent.

## Conséquences

- Les tarifs de ces deux modèles sont dans `llm/pricing.py` ; un modèle sans tarif est refusé avant tout appel.
- Haiku 5.5 n'a pas de repli automatique en cas de refus : un refus devient une erreur explicite.
