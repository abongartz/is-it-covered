# Phase 5 – Extensions

## But

Ajouter des fonctionnalités non nécessaires, une par une, par intérêt décroissant. Chaque extension est
indépendante : on peut s'arrêter après n'importe laquelle. Une extension ne doit jamais dégrader ce qui est
livré (évaluation relancée si le pipeline est touché).

## Attendus (dans l'ordre de priorité)

25. **Clé API de l'utilisateur**
    - Saisie d'une clé personnelle pour lever les plafonds, à ses frais.
    - Clé validée à la saisie, erreurs traduites, tentatives limitées.
    - Liste blanche de modèles testés, chacun avec son score d'évaluation et son coût estimé par question.
    - Toutes les règles de sécurité de `CLAUDE.md` sur les clés ; notice expliquant que la clé transite par le
      serveur sans y être stockée, et conseil d'utiliser une clé dédiée avec limite de dépense.

26. **Import de CG par l'utilisateur**
    - Import de CG non publiées sur l'outil, ou d'une édition plus récente.
    - Extraction à la volée, sous plafond de coût, avec le même schéma que le corpus.
    - Traitement pour la session uniquement : rien n'est stocké ni partagé.

27. **Clause surlignée**
    - Affichage de la page du PDF avec la citation surlignée à côté du verdict.

28. **Questions multilingues**
    - Messages en allemand ou en anglais sur des contrats en français ; réponse dans la langue du message.

29. **Import complet des CP**
    - CP scannées ou photographiées (OCR), mises en page variées, usage direct possible.
    - Mêmes garanties de confidentialité que l'import de la phase 2.

30. **Outil de mise à jour de la taxonomie**
    - Regroupement des garanties et questions classées « autre », propositions de concepts par LLM,
      revue humaine en ligne de commande, ADR à chaque changement accepté.

31. **Lois comme source secondaire**
    - Loi luxembourgeoise du 27 juillet 1997 et loi belge du 4 avril 2014 citables, séparées des clauses.

32. **Plafonds et franchises**
    - Estimation du montant indemnisable à partir des plafonds, franchises et montants des CP.

33. **Surveillance automatique des CG**
    - Vérification planifiée des sources du manifeste, détection des nouvelles éditions (y compris sous une
      nouvelle URL), différence structurée, réingestion après validation humaine.

34. **Prototype neuro-symbolique**
    - Encodage d'un contrat en logique et comparaison avec l'approche actuelle sur le jeu d'évaluation.

## Critères de fin pour chaque extension

- Définition de « terminé » de `CLAUDE.md` respectée.
- Évaluation relancée et toujours au niveau précédent si le pipeline a été modifié.
- Le site public mentionne l'extension et ses limites.
