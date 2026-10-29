# Documentation

Index de la documentation. Avant de modifier une fonctionnalité : lire sa page dans `features/` et les ADR liés ;
les mettre à jour après.

- Stratégie (document de référence) : [`strategie.md`](strategie.md)
- Phases : [`phases/`](phases/) (`phaseN.md` = attendus, `phaseN-plan.md` = plan d'action)

## Fonctionnalités

| Fonctionnalité | Page | ADR liés |
| --- | --- | --- |
| Corpus : manifeste et téléchargement | [`features/corpus.md`](features/corpus.md) | [0002](adr/0002-premier-contrat.md) |
| Parsing structurel des contrats | [`features/parsing.md`](features/parsing.md) | [0003](adr/0003-parseur-pdf.md), [0002](adr/0002-premier-contrat.md) |

## Décisions (ADR)

| N° | Titre | Statut |
| --- | --- | --- |
| [0001](adr/0001-stack.md) | Stack technique et gestion des dépendances | acceptée |
| [0002](adr/0002-premier-contrat.md) | Premier contrat : CG Assurance Habitation d'Ethias | acceptée |
| [0003](adr/0003-parseur-pdf.md) | Parseur PDF : PyMuPDF et règles par mise en page | acceptée |
