# Phase 1 – Chaîne complète sur un contrat

## But

Obtenir un premier verdict cité, de bout en bout, sur un seul contrat : extraction structurée hors ligne,
pipeline en ligne minimal, app utilisable et première version du site de documentation.
À la fin de cette phase, le projet est démontrable.

## Attendus

4. **Couche LLM**
   - Une interface unique pour obtenir des sorties structurées (Pydantic) d'un LLM, indépendante du fournisseur.
   - Un premier fournisseur branché ; changement de fournisseur ou de modèle par configuration.
   - Chaque appel enregistre tokens et coût estimé.

5. **Schéma et taxonomie v1**
   - Modèles de données pour : source (document, page, chemin de sections, texte exact, coordonnées),
     garantie (avec ses conditions, concepts, biens, lieux, caractère optionnel selon les CP),
     exclusion (portée générale ou spécifique, exceptions), définition.
   - `data/taxonomy.yaml` : une quinzaine de concepts sur l'axe des périls, facettes séparées (biens, lieux,
     statut), chaque concept avec description, exemples et notes « inclut / n'inclut pas ».

6. **Extraction du premier contrat**
   - Garanties, exclusions et définitions extraites du contrat de la phase 0, chacune avec sa source.
   - Chaque garantie rattachée à un ou plusieurs concepts avec un score de confiance ; les garanties non
     rattachées sont classées « autre ».
   - Chaque texte cité est vérifié contre le document ; les citations introuvables sont signalées.
   - Un rapport d'ingestion liste garanties non rattachées et citations invalides.
   - Exécution en synchrone, sur ce seul contrat.

7. **Pipeline en ligne minimal** (une seule question de couverture, pas encore de découpage de message)
   - Analyse du sinistre en faits typés.
   - Sélection des garanties candidates par les concepts.
   - Évaluation de chaque condition et exclusion candidate : remplie, non remplie, inconnue ou ambiguë,
     avec la clause citée ; définitions du contrat injectées.
   - Agrégation déterministe en code : couvert, non couvert ou indéterminé, avec faits manquants.
   - Vérification des citations avant restitution.

8. **App v1**
   - Choix du contrat, saisie d'un sinistre, affichage du verdict, du raisonnement condition par condition
     et des clauses citées avec leur page.
   - Déployée à l'URL publique.

9. **Documentation v1**
   - Site public sur GitHub Pages : le problème, l'architecture (schéma), les choix principaux.
   - Déploiement automatique du site à chaque push sur `main`.
   - `docs/features/` à jour pour chaque brique livrée ; ADR pour chaque choix (fournisseur, modèle, format
     de stockage, etc.).

## Critères de fin de phase

- Les deux exemples de l'énoncé (vélo dans le local commun ouvert, bougie sur la table de jardin) obtiennent
  chacun un verdict justifié, ou un « indéterminé » qui nomme ce qui manque, avec des citations vérifiées.
- Ce résultat est reproductible depuis l'app en ligne.
- Le site public est en ligne et décrit l'architecture effectivement implémentée.
- Coût LLM cumulé du projet connu et affiché dans le plan de phase.

## Hors périmètre

Découpage des messages composés, CP, plafonds de coût, autres contrats, évaluation chiffrée.
