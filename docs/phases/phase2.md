# Phase 2 – Honnêteté et robustesse

## But

Rendre l'outil fiable face à de vrais utilisateurs : messages composés, conditions particulières, questions de
clarification, cas limites et maîtrise des coûts. Toujours sur le contrat de la phase 1.

## Attendus

10. **Planificateur**
    - Un message utilisateur devient une liste de demandes typées : question de couverture, information sur le
      contrat, réponse à une question de clarification, hors périmètre.
    - Chaque question de couverture correspond à un couple (événement, bien endommagé) et porte ses propres
      faits ; les faits communs à plusieurs demandes sont recopiés dans chacune.
    - Les consignes de présentation (tableau, liste, longueur, langue) sont extraites séparément.
    - Au plus 5 demandes traitées par message ; les suivantes sont signalées à l'utilisateur.

11. **Répartition et composition**
    - Chaque question de couverture suit le pipeline de la phase 1, isolée des autres, avec ses propres
      garanties candidates.
    - La réponse finale assemble les verdicts selon les consignes ; un tableau est produit sans LLM ;
      une prose rédigée par LLM est contrôlée (chaque verdict affiché égale le verdict calculé).
    - Formats autorisés limités ; aucune consigne ne supprime les citations ni ne change un « indéterminé ».
    - Les parties hors périmètre sont listées explicitement dans la réponse.

12. **Formulaire de CP simplifiées**
    - Généré à partir de la taxonomie : formule, options souscrites, statut propriétaire ou locataire.
    - Les réponses deviennent des faits pris en compte et cités dans le raisonnement.

13. **Import des CP comme raccourci**
    - L'utilisateur peut importer ses CP (PDF texte) pour pré-remplir le formulaire, qu'il valide ensuite.
    - Données personnelles masquées avant tout appel LLM ; seuls les champs utiles sont extraits.
    - Rien n'est conservé : ni fichier, ni texte, ni données personnelles.
    - Consentement explicite et notice d'information (données traitées, finalité, durée, destinataires,
      hébergement hors UE).
    - Des CP d'exemple **fictives**, clairement marquées comme telles, servent aux tests et à la démo.
    - Fournisseur LLM compatible (pas de réutilisation des données, accord de traitement) : ADR obligatoire.

14. **Boucle de clarification**
    - Un « indéterminé » produit des questions précises sur les faits manquants.
    - Un état est conservé par demande ; chaque réponse de l'utilisateur est rattachée à la bonne demande,
      dont le verdict est recalculé.

15. **Cas limites**
    - Concept « autre » : recherche sur toutes les clauses du contrat, garanties et exclusions comprises ;
      verdict marqué comme obtenu par recherche libre ; question enregistrée pour enrichir la taxonomie.
    - Aucune clause pertinente trouvée : « indéterminé », jamais « non couvert ».
    - Terme non défini par le contrat : condition « ambiguë », signalée comme telle.

16. **Garde-fous de coût**
    - Plafonds par session, par IP et global journalier, comptés en coût estimé.
    - Longueur de saisie limitée, `max_tokens` systématique, cache des réponses identiques.
    - Résultats pré-calculés pour les deux exemples de l'énoncé, disponibles même plafond atteint.
    - Limite de dépense réglée côté fournisseur (action de l'utilisateur, à rappeler dans le plan).

## Critères de fin de phase

- Un message contenant trois sinistres différents, une question hors périmètre et une demande de tableau
  produit un tableau correct, cité, avec la partie hors périmètre signalée.
- Un même sinistre donne un verdict différent selon les options cochées dans le formulaire de CP.
- L'import d'une CP fictive pré-remplit correctement le formulaire, sans qu'aucune donnée ne soit écrite.
- Une réponse à une question de clarification fait passer un verdict de « indéterminé » à un verdict tranché.
- Les plafonds se déclenchent comme prévu (testés).
- `docs/features/` et le site public décrivent ces fonctionnalités.

## Hors périmètre

Autres contrats, évaluation chiffrée, clé API de l'utilisateur, import de CG, OCR des CP scannées.
