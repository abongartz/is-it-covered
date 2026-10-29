# Corpus : manifeste et téléchargement

## Ce que ça fait

`data/manifest.yaml` décrit chaque document du corpus ; `scripts/download_corpus.py` reconstruit `data/raw/`
à partir du manifeste en vérifiant l'empreinte SHA-256 de chaque fichier. Les PDF ne sont jamais commités.

```bash
uv run python scripts/download_corpus.py           # télécharge les documents absents
uv run python scripts/download_corpus.py --check   # vérifie les fichiers locaux, sans réseau
```

## Comment

- **Un document = (pays, assureur, produit, édition)**. Identifiant `<pays>-<assureur>-<produit>-<AAAA-MM>`,
  où la date est celle de l'édition imprimée dans le document (pas la date de téléchargement).
- Champs : pays, assureur, produit, type (`cg` ou `ipid`), langue, référence et date d'édition imprimées, URL
  source, SHA-256, date de récupération, nombre de pages. Le schéma (`isitcovered.models.corpus`) refuse tout
  champ inconnu et tout identifiant en double.
- Le téléchargement écrit d'abord un fichier `.part`, puis le renomme : pas de fichier tronqué en cas d'échec.

## Pourquoi

- **Empreinte obligatoire** : un contrat est régi par l'édition en vigueur à sa souscription ; les données
  extraites et les citations n'ont de sens que pour un fichier précis.
- **Jamais d'écrasement** : si la source ne correspond plus à l'empreinte, le script échoue sans rien écrire.
  Une source modifiée est une nouvelle édition, ajoutée au manifeste à côté de l'ancienne. Un fichier local
  corrompu n'est pas remplacé non plus : il faut le supprimer explicitement.
- **Pas de PDF dans le dépôt** : droit d'auteur des assureurs ; seuls le manifeste, le script et les données
  extraites (citations courtes) sont publiés.

## Limites connues

- Si un assureur retire un document ou change son URL, la reconstruction échoue pour ce document ; l'URL doit
  être mise à jour à la main (la surveillance automatique est une extension, phase 5).
- Aucune nouvelle tentative automatique en cas d'erreur réseau.

ADR liés : [0002](../adr/0002-premier-contrat.md).
