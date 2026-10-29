# 0004 – Validation du parsing : profil rédigé par l'agent, approuvé par un humain sur le PDF annoté

Statut : acceptée · Date : 2026-10-29

## Contexte

Le parseur reconnaît les titres avec un profil de mise en page par assureur (ADR 0003). Une erreur de
découpage (titre manqué, bloc mal rattaché, texte perdu) fausserait la portée des garanties et des exclusions
extraites ensuite, pour toutes les questions sur ce contrat. Les contrôles automatiques (sommaire imprimé,
aucune rangée de texte perdue, cohérence de l'arbre) ne voient pas tout, et relire un plan textuel de
plusieurs centaines de blocs est long et peu fiable.

Deux voies ont été discutées : garder une validation humaine par mise en page, ou automatiser entièrement le
parsing (contrôles automatiques, repli en cascade vers un profil générique, Docling ou un mode « à plat », et
dégradation des verdicts vers `indéterminé` quand la structure est douteuse). L'automatisation complète n'est
indispensable que pour l'import de CG par l'utilisateur (phase 5, extension facultative).

## Décision

- **Les règles de parsing sont rédigées par l'agent** (un profil par mise en page, comme `ethias-2025`) et
  **approuvées par un humain** avant toute extraction.
- **Support d'approbation : le PDF original annoté** (`data/parsed/<doc>/annotated.pdf`, produit par
  `scripts/parse_contract.py`) : chaque titre et chaque bloc encadré en couleur avec son identifiant, italiques
  soulignés, texte écarté signalé. Le plan textuel (`outline.md`) reste disponible en complément.
- **L'approbation est liée à la version du parseur** : `review.yaml` enregistre `approved_parser`,
  `reviewed_by`, `reviewed_at`. Un test échoue si la structure commitée a été produite par une autre version
  du parseur ou du profil : toute modification du parsing demande une nouvelle approbation.
- **Contrôles automatiques conservés** comme filet avant l'approbation : sommaire imprimé, aucune rangée perdue,
  aucun mot hors de l'arbre en dehors des en-têtes et numéros de page, italiques retrouvés.
- **Reporté (si le temps le permet)** : import de CG par l'utilisateur et, avec lui, un parsing entièrement
  automatique quelle que soit la structure du document. Il fera l'objet d'un ADR dédié.
- Le contrat Ethias (édition 03/25) est approuvé le 2026-10-29 avec le parseur `pymupdf-rules/ethias-2025@1`.

## Alternatives

- **Parsing entièrement automatique dès maintenant** : nécessaire pour l'import de CG, mais demande un parseur
  générique, une cascade de replis et une notion de qualité de structure propagée jusqu'au verdict. Coût élevé
  pour un corpus d'environ 8 contrats dont les mises en page sont connues à l'avance.
- **Relecture du plan textuel** : plus lente, et les erreurs de position (bloc rattaché à la mauvaise section,
  texte oublié) ne s'y voient pas.
- **Contrôles automatiques seuls, sans humain** : ne détectent pas un titre reconnu mais mal hiérarchisé
  lorsqu'il n'apparaît pas au sommaire (sous-articles, intitulés).

## Conséquences

- Chaque nouvelle mise en page coûte un profil et une approbation humaine (une lecture du PDF annoté, de
  l'ordre de 15 minutes) ; les éditions suivantes d'un même assureur réutilisent le profil, mais une
  approbation reste nécessaire par document.
- Modifier le parseur invalide les approbations existantes : on évite les modifications non nécessaires et on
  regroupe les corrections.
- Limite connue : le cadre d'un titre sur deux lignes ne couvre que la première ligne (le titre lui-même est
  complet) ; à corriger lors d'une prochaine version du parseur.
- Les erreurs d'extraction des objets typés (phase 1) restent traitées par ce que prévoit la stratégie
  (citations vérifiées par programme, évaluation) ; des parades supplémentaires pourront être décidées plus tard.
