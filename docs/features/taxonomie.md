# Taxonomie

## Ce que ça fait

`data/taxonomy.yaml` donne une langue commune entre les mots de l'utilisateur et ceux de chaque contrat :
15 concepts de périls + `other`, et trois facettes (biens, lieux, statut). Elle **oriente** la sélection des
garanties candidates ; elle ne définit rien, le sens juridique vient toujours du contrat analysé.
Le schéma est `isitcovered.models.taxonomy` (`Taxonomy`, `Concept`, `FacetValue`).

## Comment

- **Concept** : `id` stable (anglais), `label`, `description`, `examples` (sinistres tels qu'un assuré les
  décrit), `includes`, `excludes`, `deprecated_by` éventuel. Le texte est en français : c'est ce que lit le
  LLM pour rattacher une garantie (ingestion) et orienter un sinistre (en ligne).
- **Facettes** : `assets` (bâtiment, contenu, vélos, mobilier de jardin…), `locations` (logement,
  dépendances, parties communes, jardin, hors du domicile), `status` (propriétaire, locataire, autre
  occupant). Les garanties et les faits d'un sinistre portent des identifiants de facettes.
- **Validation** au chargement : identifiants uniques par groupe, `other` présent, `deprecated_by` vers un
  concept existant.

## Pourquoi

- **Un seul axe de concepts** (les périls) : c'est ainsi que les contrats organisent leurs garanties ; les biens
  et les lieux sont des facettes indépendantes, combinables.
- **Une quinzaine de concepts** : assez pour filtrer, assez peu pour un rattachement stable et vérifiable à la
  main (les IPID listent une dizaine à une quinzaine de garanties).
- **Rappel d'abord** : les notes « inclut » ratissent large (la chaleur qui fait fondre une table relève de
  `fire`), parce qu'une garantie manquée est pire qu'une garantie de trop, évaluée puis écartée.

## Vérification

- `tests/test_models.py` : la taxonomie se charge, compte entre 13 et 17 concepts de périls, chacun avec
  description, exemples et notes ; les facettes attendues par les exemples (vélo, mobilier de jardin, parties
  communes) existent ; doublons et dépréciations orphelines sont refusés.

## Limites connues

- Les notes « inclut / n'inclut pas » sont rédigées a priori ; elles seront ajustées d'après le rapport
  d'ingestion (garanties `other`) et l'évaluation, chaque changement de concept par un ADR.

ADR liés : [0012](../adr/0012-taxonomie-v1.md).
