# Parsing structurel des contrats

## Ce que ça fait

Convertit le PDF d'un contrat en **arbre de sections** : chapitres, articles, sous-articles, subdivisions et
termes du lexique, chacun avec son titre, ses pages et ses coordonnées, et découpé en **blocs de texte**
(paragraphe, élément de liste, intitulé en gras, note de bas de page) avec page et coordonnées.
L'arbre est contrôlé automatiquement (sommaire imprimé, texte perdu), puis **approuvé par un humain sur le PDF
original annoté**, qui montre chaque titre et chaque bloc encadré en couleur ([ADR 0004](../adr/0004-validation-du-parsing.md)).

```bash
uv run --group ingestion python scripts/parse_contract.py [DOC_ID ...]
```

| Fichier | Contenu | Publié |
| --- | --- | --- |
| `data/parsed/<doc>/sections.json` | arbre complet avec le texte | non (régénéré localement) |
| `data/parsed/<doc>/outline.md` | plan lisible avec extraits | non |
| `data/parsed/<doc>/annotated.pdf` | PDF original avec l'arbre dessiné par-dessus, support de l'approbation | non |
| `data/contracts/<doc>/structure.json` | arbre sans le texte (titres, pages, coordonnées, nombre de blocs) | oui |
| `data/contracts/<doc>/toc_check.json` | comparaison avec le sommaire imprimé | oui |
| `data/contracts/<doc>/review.yaml` | écarts vérifiés au sommaire ; approbation (version du parseur, relecteur, date) | oui |

Le modèle est dans `isitcovered.models.sections` (`SectionTree`, `Section`, `TextBlock`).

## Comment

1. **Lignes → rangées.** PyMuPDF donne les lignes et leurs fragments (police, taille, couleur, coordonnées).
   Les lignes qui partagent une ligne de base sont regroupées en une rangée (« 1.1. » et son titre, une puce et
   son texte). Les fragments d'une même ligne sont concaténés sans espace ; deux lignes distinctes, avec un espace.
2. **Éléments de page retirés.** En-tête courant (rangée du haut de page répétée sur au moins 30 % des pages) et
   numéros de page (rangée du bas de page purement numérique). Les notes de bas de page (`* Indice ABEX…`) sont
   conservées comme blocs `footnote`.
3. **Titres reconnus par un profil de mise en page**, un par mise en page d'assureur. Pour Ethias :
   - chapitre : gras ≥ 13,5 pt, `Chapitre <romain>` ;
   - article : gras 10 pt **blanc** (bandeau), `Article <n>` ;
   - sous-article : gras 10 pt en marge gauche, `<n>.<n>.` ;
   - intitulé non numéroté : gras 10 pt ; subdivision lettrée : gras 9 pt, `A.` ;
   - terme du lexique : gras 9 pt dans le chapitre « Lexique » ;
   - couverture (page 1) et quatrième de couverture (dernière page) ne sont jamais découpées en titres ;
   - un titre qui passe à la ligne (même style, aligné, juste en dessous) est recollé.
4. **Arbre.** Le niveau vient de la numérotation (`4.2` → 3, `4.2.1` → 4) ; un intitulé non numéroté est
   rattaché à la section numérotée la plus profonde. Identifiants stables dérivés de la numérotation :
   `ch-iii`, `art-4`, `art-4.2`, `art-13.1/A`, `art-9.1/h1`, `def-incendie`.
5. **Blocs.** Une rangée commence un nouveau bloc si elle commence par une puce, change de graisse, change de
   page, recule en retrait ou si l'écart de ligne de base dépasse 13 pt (interligne de 11 pt).
   Les passages **en italique** sont relevés dans chaque bloc : chez Ethias, l'italique signale un terme défini
   au lexique, ce qui servira à injecter les définitions en phase 1.
6. **Contrôle contre le sommaire.** Le sommaire imprimé est relu (une entrée par ligne, titre recollé s'il est
   sur deux lignes) et comparé à l'arbre : chaque chapitre et article doit exister, avec le même titre et la même
   page, et l'arbre ne doit pas contenir de chapitre ou d'article absent du sommaire. Un écart vérifié dans le
   PDF et imputable au document est consigné dans `review.yaml` avec sa justification.
7. **PDF annoté** (`ingestion/annotate.py`). Le PDF original est recopié avec, par-dessus, un cadre par titre
   (couleur selon le type, identifiant en marge en gras) et par bloc (couleur selon le type,
   `section #n · type` en marge), les italiques soulignés et, en pointillés rouges, chaque mot qui n'appartient
   à aucun bloc ni titre. Une page de légende est ajoutée en tête, avec les compteurs de contrôle.
8. **Approbation.** Un humain parcourt le PDF annoté ; son accord est consigné dans `review.yaml`
   (`approved_parser`, `reviewed_by`, `reviewed_at`). L'approbation vaut pour une version du parseur et du
   profil : si l'une change, le test d'approbation échoue jusqu'à une nouvelle relecture.

## Pourquoi

- **Règles plutôt que modèle** : déterministe, rapide, gratuit, et chaque décision est explicable. Les titres des
  CG sont très réguliers ; la variabilité entre assureurs est absorbée par un profil par mise en page plutôt que
  par un modèle généraliste (voir [ADR 0003](../adr/0003-parseur-pdf.md)).
- **Le sommaire imprimé comme vérité terrain** : il est produit par l'assureur, indépendant du parseur, et
  donne un contrôle automatique à chaque modification.
- **Texte non publié** : un arbre avec le texte intégral reviendrait à republier les CG. Seule la structure est
  commitée ; le texte est régénéré localement à partir du PDF (empreinte vérifiée).
- **Coordonnées conservées** : elles permettront de surligner la clause citée dans l'image de la page (phase 5).
- **Approbation sur le PDF annoté plutôt que sur un plan textuel** : les erreurs de position (bloc rattaché à la
  mauvaise section, texte oublié, liste mal découpée) se voient d'un coup d'œil sur la page d'origine.
  L'automatisation complète, nécessaire seulement pour l'import de CG par l'utilisateur, est reportée.

## Vérification

- Tests sur un PDF synthétique généré dans les tests (hiérarchie, blocs, italiques, en-têtes retirés, sommaire).
- Tests sur le contrat réel quand le PDF est présent (en CI, il est téléchargé) : la structure régénérée est
  identique à la structure commitée, **aucune rangée de texte n'est perdue** (chacune se retrouve dans un
  bloc ou un titre), et sur le PDF annoté aucun mot n'est hors de l'arbre en dehors des en-têtes, des numéros
  de page et des suites de titres ; tous les italiques sont retrouvés.
- L'approbation enregistrée dans `review.yaml` porte sur la version du parseur qui a produit la structure.
- Ethias, édition 03/25 : 7 chapitres, 21 articles, 83 sous-articles, 53 termes ; sommaire conforme
  (29 entrées), un écart accepté : le sommaire imprimé place l'article 20 page 29, il commence page 30.
  Approuvé le 2026-10-29 sur le PDF annoté (`pymupdf-rules/ethias-2025@1`).

## Limites connues

- Un profil par mise en page : un nouvel assureur demande un nouveau profil (quelques règles) ; Docling reste
  l'option de repli si une mise en page résiste aux règles.
- Les listes imbriquées sont aplaties (le niveau d'imbrication n'est visible que dans l'abscisse du bloc).
- Un paragraphe coupé par un saut de page donne deux blocs (un par page), ce qui simplifie les citations.
- Les tableaux ne sont pas reconnus comme tels (aucun dans le contrat Ethias).
- Pas d'OCR : les PDF scannés ne sont pas pris en charge.
- Le cadre d'un titre sur deux lignes ne couvre que sa première ligne (le titre est complet ; seules les
  coordonnées sont partielles, par exemple l'article 21 d'Ethias).
- Chaque document demande une approbation humaine : pas de parsing entièrement automatique, donc pas encore
  d'import de CG par l'utilisateur.

ADR liés : [0003](../adr/0003-parseur-pdf.md), [0004](../adr/0004-validation-du-parsing.md),
[0002](../adr/0002-premier-contrat.md).
