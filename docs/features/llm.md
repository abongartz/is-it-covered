# Couche LLM et suivi des coûts

## Ce que ça fait

Tout appel à un LLM passe par un `LLMClient` (`src/isitcovered/llm/`) : l'appelant fournit un prompt système,
des messages, un **schéma Pydantic** et un `max_tokens` ; il reçoit une instance validée, les tokens consommés
et le coût estimé. Les scripts hors ligne inscrivent chaque appel dans `data/costs/ledger.jsonl` (commité).

```bash
uv run python scripts/llm_smoke.py --count-only   # comptage des tokens du prompt (gratuit)
uv run python scripts/llm_smoke.py                # un appel réel minuscule (route facts, < 0,01 $)
```

## Comment

| Module | Rôle |
| --- | --- |
| `base.py` | protocole `LLMClient`, `LLMResult`, `Usage`, erreurs (`LLMConfigError`, `LLMUnavailableError`, `LLMRefusalError`, `LLMTruncatedError`, `LLMInvalidOutputError`) |
| `config.py` | routes `ingestion`, `linking`, `facts`, `evaluation` → fournisseur, modèle, effort ; surcharge par `ISITCOVERED_MODEL_<ROUTE>=fournisseur/modèle` et `ISITCOVERED_EFFORT_<ROUTE>` |
| `pricing.py` | tarifs en USD par M tokens (entrée, sortie ; lecture de cache × 0,1, écriture × 1,25 ; second barème pour les prompts longs) |
| `ledger.py` | journal JSONL : date, route, modèle, effort, tokens, coût, issue (`ok` ou nom de l'erreur) |
| `keys.py` | clé locale lue dans `ISITCOVERED_ANTHROPIC_API_KEY` |
| `anthropic_client.py` | adaptateur Anthropic, seul module qui importe le SDK |
| `fake.py` | client simulé qui rejoue des sorties enregistrées (tests) |

Déroulé d'un appel (`AnthropicClient.structured`) :

1. Route → configuration ; refus immédiat si le fournisseur n'est pas le bon ou si le modèle n'a pas de tarif.
2. Requête `messages.create` : modèle exact, `max_tokens`, effort, schéma JSON (`output_config.format`), prompt
   système marqué pour le cache de prompt. Ni `temperature` ni réflexion forcée.
3. Lecture de l'usage, puis de `stop_reason` : `refusal` → `LLMRefusalError` ; `max_tokens` ou contexte dépassé
   → `LLMTruncatedError` ; sinon validation Pydantic du texte → `LLMInvalidOutputError` en cas d'échec.
4. Coût estimé et inscription au journal **avant** de lever l'éventuelle erreur : un appel raté a coûté.

## Pourquoi

- **Indépendance du fournisseur** : le pipeline ne connaît que le protocole ; un changement de modèle est une
  variable d'environnement, un changement de fournisseur un adaptateur de plus (ADR 0005).
- **`create` plutôt que `parse`** : `messages.parse()` valide la sortie avant que l'on puisse lire
  `stop_reason` ; une sortie tronquée deviendrait une erreur de validation trompeuse.
- **Pas de streaming** : les sorties attendues sont courtes ; le délai d'attente est fixé explicitement
  (600 s) pour que le SDK accepte un `max_tokens` élevé sans streaming.
- **Erreurs sans détail** : les erreurs du SDK sont converties en `LLMError` avec seulement leur nature et leur
  code HTTP (`raise … from None` : la trace d'origine, avec la requête, n'est pas chaînée). Seule l'explication
  d'une erreur 400 (paramètre refusé) est gardée, tronquée : elle ne contient ni en-têtes ni clé.
- **Journaux HTTP désactivés** : les loggers `anthropic`, `httpx2`, `httpx`, `httpcore` sont au niveau
  `WARNING`.
- **Clé** : jamais sur disque. En local, `ISITCOVERED_ANTHROPIC_API_KEY` (et non `ANTHROPIC_API_KEY`, que
  Claude Code utiliserait pour lui-même) ; sur l'hébergeur, `st.secrets["ANTHROPIC_API_KEY"]` lu par l'app.
  La clé est toujours passée explicitement au SDK.
- **Reproductibilité** : version de modèle et effort figés, sorties commitées (ADR 0007).

## Vérification

- `tests/test_llm.py`, sans réseau : calcul des coûts (barèmes, cache), routage et surcharges invalides,
  journal (aucun champ de contenu), client simulé, adaptateur contre un transport HTTP simulé (corps de la
  requête, sortie validée, refus, troncature, sortie invalide, coût inscrit malgré l'échec, erreurs 400 à 404
  sans la clé ni la cause chaînée, comptage des tokens), et aucun module hors de l'adaptateur n'importe le SDK.

## Limites connues

- Les tarifs sont recopiés à la main (relevés le 2026-10-29) : à mettre à jour si le fournisseur les change.
- Le coût est une estimation à partir de l'usage renvoyé ; la facture fait foi.
- Le cache de prompt ne s'active qu'au-delà d'une taille minimale de préfixe (512 tokens sur ces modèles).

ADR liés : [0005](../adr/0005-fournisseur-llm.md), [0006](../adr/0006-modeles-llm.md),
[0007](../adr/0007-reproductibilite-sans-temperature.md).
