# Phase 4 – Évaluation et documentation complète

## But

Mesurer la qualité de l'outil avec des chiffres, justifier les choix par ces chiffres, et livrer un site de
documentation complet. C'est la phase qui rend le projet présentable au recruteur.

## Attendus

22. **Jeu d'évaluation**
    - 20 à 30 cas annotés à la main sur au moins 3 contrats, dont les deux exemples de l'énoncé.
    - Chaque cas : contrat, message, CP simulées, verdict attendu, clauses attendues, faits manquants attendus.
    - Des cas ambigus, des cas hors périmètre, un même sinistre sur deux contrats aux définitions différentes,
      et des messages composés (plusieurs sinistres, partie hors périmètre, consigne de format).
    - Un script qui exécute le jeu et écrit `eval/results.json` (date, commit, modèle compris).
    - Métriques : justesse du verdict ; faux « couvert » et faux « non couvert » comptés séparément ; qualité de
      l'abstention ; citations valides ; citations pertinentes ; qualité du découpage des messages ; coût et
      latence par question.

23. **Référence et comparaison de modèles**
    - Comparaison avec une approche « contrat entier dans le prompt » sur le même jeu.
    - Comparaison d'au moins deux modèles pour le pipeline en ligne (par exemple Haiku 4.5 et Mistral Small),
      qualité et coût.
    - Le modèle en ligne retenu est justifié par ces chiffres dans un ADR.

24. **Documentation complète**
    - Le site public couvre : le problème ; pourquoi l'approche naïve échoue ; l'assurance en 2 minutes
      (CG, CP, IPID, Belgique et Luxembourg) ; l'architecture ; le modèle de données ; la taxonomie ;
      un pas à pas réel sur le vélo et la bougie ; l'évaluation ; les choix et alternatives ; les limites et
      perspectives ; les coûts.
    - Tous les chiffres, la taxonomie, le corpus et les traces d'exemple sont lus depuis les JSON produits par
      le code ; chaque bloc chiffré affiche date, commit et modèle.
    - Schémas et graphiques soignés ; lisible sur téléphone.
    - L'app affiche aussi un résumé de l'évaluation et renvoie vers le site.

## Critères de fin de phase

- `eval/results.json` existe et correspond au code de `main`.
- Le site présente les résultats d'évaluation, la comparaison avec la référence et la comparaison de modèles.
- Un lecteur qui ne connaît pas le projet comprend, depuis le site seul, ce que fait l'outil, comment, pourquoi,
  et ce qu'il ne fait pas.
- README, app, site et `docs/` sont cohérents entre eux.

## Hors périmètre

Extensions de la phase 5.
