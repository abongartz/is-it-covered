# 0005 – Fournisseur LLM : Anthropic, SDK officiel derrière `LLMClient`

Statut : acceptée · Date : 2026-10-29

## Contexte

La stratégie prévoit une abstraction `LLMClient` indépendante du fournisseur et des sorties structurées
validées par Pydantic. Il faut un premier fournisseur, avec le moins de dépendances possible (surface d'attaque,
taille de l'app hébergée) et des sorties structurées fiables.

## Décision

- **Anthropic**, via le **SDK officiel `anthropic`** (version exacte figée dans `pyproject.toml` et `uv.lock`).
- Sorties structurées natives de l'API (`output_config.format`, schéma JSON généré depuis le modèle Pydantic),
  puis validation Pydantic par notre code, **après** vérification de `stop_reason`.
- Le protocole `LLMClient` (`src/isitcovered/llm/base.py`) expose `structured()` et `count_tokens()`.
  `llm/anthropic_client.py` est le seul module qui importe le SDK (test dédié) ; le code de batch d'ingestion
  pourra l'importer aussi.
- Le fournisseur et le modèle se choisissent par route, par configuration (`provider/modèle`) ; un second
  fournisseur s'ajoutera par un nouvel adaptateur derrière le même protocole.

## Alternatives

- **Instructor** (prévu par la stratégie) : multi-fournisseur immédiat, mais plusieurs dépendances de plus, et
  inutile tant qu'il n'y a qu'un fournisseur.
- **LiteLLM** : très large surface (et incident de chaîne d'approvisionnement connu) ; écarté.
- **`messages.parse()` du SDK** : valide la sortie avant que l'on puisse lire `stop_reason`, si bien qu'une
  sortie tronquée lève une erreur de validation au lieu d'une erreur « tronquée » explicite ; on utilise
  `messages.create()` avec le même schéma.

## Conséquences

- Une seule dépendance ajoutée (et ses dépendances : `httpx2`, `jiter`, `anyio`…), également installée sur
  l'hébergeur.
- Changer de fournisseur demande un adaptateur et ses tarifs, pas de modification du pipeline.
