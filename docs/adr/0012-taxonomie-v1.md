# 0012 – Taxonomie v1 et rattachement des garanties

Statut : acceptée · Date : 2026-10-29

## Contexte

Les concepts de la taxonomie servent à sélectionner les garanties candidates d'un sinistre, sans jamais en
définir le sens. La stratégie prévoit un seul axe de concepts (les périls, une quinzaine) et des facettes
séparées.

## Décision

- `data/taxonomy.yaml`, version 1 : **15 concepts de périls** (`fire`, `storm_hail_snow`, `water_damage`,
  `natural_disasters`, `glass_breakage`, `theft_vandalism`, `electrical_damage`, `impact`,
  `terrorism_labour_conflicts`, `building_liability`, `private_liability`, `tenant_liability`,
  `legal_protection`, `assistance`, `accidental_damage`) + **`other`**. Chaque concept : libellé,
  description, exemples de sinistres, notes « inclut / n'inclut pas » (en français : c'est ce que lit le LLM).
- **Facettes** : biens (12 valeurs, dont `bicycles` et `garden_furniture`), lieux (5, dont `common_areas`),
  statut (`owner`, `tenant`, `other_occupant`).
- Identifiants en anglais, stables, jamais renommés ni réutilisés ; un concept retiré reçoit `deprecated_by`.
- **Rattachement** par un appel LLM séparé de l'extraction (taxonomie + garanties extraites → concepts avec
  confiance 0–1) ; seuil 0,5, sinon `other` ; les garanties `other` sont listées au rapport d'ingestion.
- Les notes « inclut » favorisent le **rappel** (une bougie qui fait fondre une table oriente vers `fire`) :
  l'évaluation de la garantie reste stricte.

## Alternatives

- **Rattachement dans l'appel d'extraction** : prompt plus long, taxonomie répétée à chaque unité.
- **Plus de concepts** (par exemple séparer explosion et incendie) : rattachement moins stable, pas de gain de
  sélection, puisque les garanties proches sont de toute façon évaluées ensemble.

## Conséquences

- Toute modification d'un concept passe par un ADR.
- Les garanties accessoires (frais connexes, pertes indirectes) relèveront souvent de `other` : leur
  sélection en ligne (lien avec la garantie principale ou recherche) est à préciser avec le pipeline.
