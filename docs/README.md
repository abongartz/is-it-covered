# Documentation

Index de la documentation. Avant de modifier une fonctionnalité : lire sa page dans `features/` et les ADR liés ;
les mettre à jour après.

- Stratégie (document de référence) : [`strategie.md`](strategie.md)
- Phases : [`phases/`](phases/) (`phaseN.md` = attendus et plan d'action ; phase en cours :
  [phase 1](phases/phase1.md))

## Fonctionnalités

| Fonctionnalité | Page | ADR liés |
| --- | --- | --- |
| Corpus : manifeste et téléchargement | [`features/corpus.md`](features/corpus.md) | [0002](adr/0002-premier-contrat.md) |
| Parsing structurel des contrats | [`features/parsing.md`](features/parsing.md) | [0003](adr/0003-parseur-pdf.md), [0004](adr/0004-validation-du-parsing.md), [0002](adr/0002-premier-contrat.md) |
| Couche LLM et suivi des coûts | [`features/llm.md`](features/llm.md) | [0005](adr/0005-fournisseur-llm.md), [0006](adr/0006-modeles-llm.md), [0007](adr/0007-reproductibilite-sans-temperature.md) |
| Extraction structurée des contrats | [`features/extraction.md`](features/extraction.md) | [0008](adr/0008-unites-extraction.md), [0009](adr/0009-stockage-extraction.md), [0010](adr/0010-verification-citations.md), [0011](adr/0011-definitions.md) |
| Taxonomie | [`features/taxonomie.md`](features/taxonomie.md) | [0012](adr/0012-taxonomie-v1.md) |

## Décisions (ADR)

| N° | Titre | Statut |
| --- | --- | --- |
| [0001](adr/0001-stack.md) | Stack technique et gestion des dépendances | acceptée |
| [0002](adr/0002-premier-contrat.md) | Premier contrat : CG Assurance Habitation d'Ethias | acceptée |
| [0003](adr/0003-parseur-pdf.md) | Parseur PDF : PyMuPDF et règles par mise en page | acceptée |
| [0004](adr/0004-validation-du-parsing.md) | Validation du parsing : profil rédigé par l'agent, approuvé sur le PDF annoté | acceptée |
| [0005](adr/0005-fournisseur-llm.md) | Fournisseur LLM : Anthropic, SDK officiel derrière `LLMClient` | acceptée |
| [0006](adr/0006-modeles-llm.md) | Modèles : Sonnet 5.5 hors ligne, Haiku 5.5 en ligne | acceptée |
| [0007](adr/0007-reproductibilite-sans-temperature.md) | Reproductibilité sans température | acceptée |
| [0008](adr/0008-unites-extraction.md) | Unités d'extraction et portée des exclusions | acceptée |
| [0009](adr/0009-stockage-extraction.md) | Stockage de l'extraction : JSON commité avec les extraits cités | acceptée |
| [0010](adr/0010-verification-citations.md) | Vérification des citations : deux niveaux, comparaison normalisée | acceptée |
| [0011](adr/0011-definitions.md) | Définitions : lexique converti par le code, injection ciblée en ligne | acceptée |
| [0012](adr/0012-taxonomie-v1.md) | Taxonomie v1 et rattachement des garanties | acceptée |
