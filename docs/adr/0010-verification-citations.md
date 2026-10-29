# 0010 – Vérification des citations : deux niveaux, comparaison normalisée

Statut : acceptée · Date : 2026-10-29

## Contexte

Toute affirmation sur un contrat cite sa source, et chaque citation est vérifiée par programme avant d'être
affichée. Une comparaison stricte rejetterait des citations correctes : le contrat mélange apostrophes
typographiques et droites et garde des artefacts de coupure (« et/ ou ») que le LLM recopie mal.

## Décision

- **Hors ligne** (ingestion) : chaque extrait doit se retrouver dans le bloc cité de l'arbre approuvé.
- **En ligne** (évaluation) : chaque citation de l'évaluateur doit se retrouver dans un extrait déjà vérifié de
  la clause citée (l'app n'a pas le PDF, ADR 0009). Une citation invalide fait passer le jugement concerné à
  `unknown`.
- **Normalisation** (`isitcovered/textmatch.py`), appliquée aux deux textes : Unicode NFKC ; apostrophes
  (’ ‘ ʼ → ') ; guillemets (« » “ ” → ") ; tirets (– — ‑ → -) ; casse ignorée ; **tous les espaces
  supprimés**.
- **Longueur minimale** : 15 caractères normalisés, sauf si l'extrait couvre tout le texte source (un titre
  comme « La foudre »).
- **Texte conservé** : le passage correspondant **du bloc source**, retrouvé par une table de correspondance
  entre positions normalisées et positions d'origine ; jamais le texte du LLM.

## Alternatives

- **Égalité stricte** : faux rejets (apostrophes, espaces, coupures).
- **Similarité approximative** (distance d'édition) : accepterait des citations légèrement altérées, dont le
  sens peut changer (« non » ajouté ou retiré).
- **Vérification en ligne contre le PDF** : impossible sans le PDF sur l'hébergeur.

## Conséquences

- Une citation qui retire ou ajoute des mots est rejetée ; seule la typographie est tolérée.
- La suppression des espaces pourrait, en théorie, faire correspondre deux découpages différents des mêmes
  lettres ; le risque est négligeable pour des extraits d'au moins 15 caractères.
