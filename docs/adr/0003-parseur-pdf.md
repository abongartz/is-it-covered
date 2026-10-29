# 0003 – Parseur PDF : PyMuPDF et règles par mise en page

Statut : acceptée · Date : 2026-10-29

## Contexte

Les CG doivent être converties hors ligne en arbre de sections avec pages et coordonnées, pour que chaque
garantie, exclusion ou définition extraite en phase 1 garde une source précise. Le parsing ne doit rien
imposer à l'app déployée (peu de mémoire). Le premier contrat (Ethias) n'a pas de signets PDF mais a un sommaire
imprimé et une typographie très régulière.

## Décision

- **PyMuPDF** pour lire les PDF (texte, police, taille, couleur, coordonnées au niveau du fragment), dans le
  groupe de dépendances `ingestion`, jamais installé sur l'hébergeur.
- **Reconnaissance des titres par règles**, regroupées dans un **profil de mise en page** par assureur
  (numérotation + typographie), avec contrôle automatique contre le sommaire imprimé.
- **Seule la structure est publiée** (`data/contracts/<doc>/structure.json`) ; l'arbre avec le texte intégral
  reste local (`data/parsed/`, ignoré par git) et se régénère à partir du PDF.

## Alternatives

- **Docling** : modèles de mise en page, meilleur sur les documents complexes (colonnes, tableaux), mais lourd
  (PyTorch, modèles à télécharger), plus lent, moins prévisible ; sa hiérarchie de titres est souvent aplatie et
  devrait de toute façon être reconstruite par règles. Gardé comme repli si un contrat résiste aux règles.
- **pdfplumber / pdfminer** : équivalents en données, plus lents, sans avantage ici.
- **LLM sur les pages** : coûteux, non déterministe, et pas nécessaire pour une structure aussi régulière.
- **Signets PDF** : absents du contrat Ethias, donc inutilisables comme source principale.
- **Publier l'arbre avec le texte** : plus simple pour les tests, mais republie de fait les CG (droit d'auteur).

## Conséquences

- Chaque nouvelle mise en page demande un profil (quelques règles) et un contrôle contre son sommaire.
- **Licence** : PyMuPDF est sous AGPL-3.0. Sans conséquence ici : le dépôt est public et PyMuPDF ne tourne pas
  sur le serveur. À réexaminer si PyMuPDF est utilisé en ligne (import de CG, phase 5).
- Les tests de reproductibilité sur le contrat réel ont besoin du PDF : la CI le télécharge avant les tests.
