# Phase 0 – Fondations

## But

Disposer d'un projet en ligne dès le départ : dépôt structuré, app publique minimale, premier contrat
téléchargé et découpé en sections. Aucun appel LLM dans cette phase.

## Attendus

1. **Squelette déployé**
   - Dépôt GitHub public organisé selon l'arborescence de `CLAUDE.md`.
   - Dépendances figées avec fichier de verrouillage.
   - `.gitignore` excluant au minimum `data/raw/` et les secrets.
   - App Streamlit minimale accessible à une URL publique, secrets configurés sur l'hébergeur.
   - `.streamlit/config.toml` avec l'affichage des détails d'erreur désactivé.
   - `docs/README.md` (index vide mais structuré), `docs/adr/` avec un premier ADR sur la stack retenue.
   - README court avec le lien vers l'app.

2. **Premier contrat**
   - Un jeu de CG habitation d'un assureur du périmètre, téléchargé depuis sa source publique.
   - `data/manifest.yaml` décrivant ce document : pays, assureur, produit, référence et date d'édition,
     URL source, empreinte SHA-256, date de récupération.
   - Un script qui retélécharge les documents du manifeste et vérifie leur empreinte.
   - Le PDF n'est pas commité.

3. **Parsing structurel**
   - Le PDF du premier contrat est converti en arbre de sections (titres hiérarchisés, texte, numéros de page,
     coordonnées des blocs) enregistré en JSON.
   - Le parsing tourne hors ligne ; aucune dépendance lourde n'est requise par l'app déployée.

## Critères de fin de phase

- L'URL publique de l'app répond.
- L'arbre de sections du premier contrat a été relu et correspond au sommaire du document.
- Le script de téléchargement reconstruit `data/raw/` à partir du manifeste sur une machine vierge.
- `docs/features/` contient une page sur le parsing ; au moins un ADR existe.

## Hors périmètre

Appels LLM, extraction des garanties, taxonomie, site public de documentation.
