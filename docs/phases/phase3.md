# Phase 3 – Passage à l'échelle du corpus

## But

Passer d'un contrat à huit, sans modifier le pipeline en ligne, et montrer que le même sinistre peut recevoir des
verdicts différents selon le contrat.

## Attendus

17. **Corpus complet**
    - 4 assureurs habitation au Luxembourg et 4 en Belgique (Foyer Belgium inclus s'il n'est pas dans les 4).
    - CG quand elles sont légalement accessibles, IPID sinon ; chaque document décrit dans le manifeste.
    - Le classement retenu et les documents inaccessibles sont justifiés dans un ADR.

18. **Ingestion en batch**
    - Prompts d'extraction mis au point en synchrone avant le passage complet.
    - Ingestion du corpus en mode batch (accord de l'utilisateur et coût estimé annoncé avant lancement).
    - Validation de chaque sortie à la réception ; reprise des sorties invalides.
    - Un rapport d'ingestion global : garanties par contrat, taux de rattachement, citations invalides.
    - Un moyen de secours synchrone si le batch tarde.

19. **Page « Contrats »**
    - Pour chaque contrat : garanties, concepts rattachés, exclusions, définitions, scores de confiance,
      date d'édition et source.

20. **Choix de l'édition des CG**
    - La date d'édition utilisée est affichée avec chaque verdict.
    - Quand plusieurs éditions existent, l'utilisateur choisit ; présélection si la référence d'édition a été
      lue dans des CP importées.

21. **Comparaison entre contrats**
    - Un même sinistre analysé sur plusieurs contrats, verdicts présentés côte à côte avec leurs citations.

## Critères de fin de phase

- 8 contrats (ou IPID) ingérés, rapport d'ingestion produit et relu.
- Aucune modification du pipeline en ligne n'a été nécessaire pour ajouter les contrats ; si une modification
  l'a été, elle est justifiée dans un ADR.
- La comparaison montre au moins un cas où deux contrats donnent deux verdicts différents, chacun justifié par
  son propre texte.
- Coût cumulé du projet toujours sous le budget.

## Hors périmètre

Évaluation chiffrée, surveillance automatique des CG, import de CG par l'utilisateur.
