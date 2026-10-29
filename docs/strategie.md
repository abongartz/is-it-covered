# Stratégie – Analyse de couverture de sinistres

Oct 29, 2026 · @Antoine

## Contexte et objectifs

Le projet est un outil qui détermine si un sinistre est couvert par un contrat d'assurance habitation, en citant les clauses et en s'abstenant quand le contrat ne permet pas de conclure. Il répond à un exercice technique proposé par un recruteur, à livrer en environ 24 h sous forme déployée.

**Ce que le recruteur évalue** (d'après l'énoncé) :

- la capacité à **citer ses sources** et à **admettre ses limites** quand le contrat est ambigu ; un « je ne sais pas » étayé vaut mieux qu'un verdict assuré sans justification ;
- ce qui remplace « injecter le document brut dans un chatbot », qui marche sur un contrat et s'écroule ensuite ;
- la réponse à la question : **comment tenir des centaines de contrats différents ?**

**Cas d'exemple de l'énoncé** :

1. Vélo volé dans le local commun de l'immeuble, non fermé à clé.
2. Bougie laissée sur la table de jardin pendant les vacances, qui fond et abîme la table.

**Critères de réussite** : une URL publique fonctionnelle, un dépôt GitHub public, un site de documentation soigné et à jour qui explique les choix et présente l'évaluation, un coût total sous 20 €.

**Ressource fournie par le recruteur** : [Parse the folder, not just the PDFs](https://towardsdatascience.com/parse-the-folder-not-just-the-pdfs-the-relational-tables-rag-needs-on-a-case-file/) (Towards Data Science). Idées reprises : structurer d'abord, appeler le LLM ensuite ; sorties typées avec citation ; l'absence et le doute comme réponses à part entière ; évaluation locale qui compte les types d'erreur séparément.

## Comprendre la donnée

Le corpus couvre l'assurance habitation de deux pays, Luxembourg et Belgique, avec les 4 plus gros assureurs de chacun (plus Foyer Belgium s'il n'en fait pas partie). Le schéma reste extensible à d'autres assureurs et pays.

### Les documents d'un contrat

| Document | Contenu | Public ? | Rôle dans l'outil |
| --- | --- | --- | --- |
| Conditions générales (CG) | Garanties, exclusions, lexique ; identiques pour tous les clients d'un produit (30 à 80 pages) | Souvent, pas toujours | Source principale, pré-ingérée |
| Conditions particulières (CP) | Formule, options souscrites, adresse, montants, franchise ; prime sur les CG | Non (données personnelles) | Formulaire simplifié, pré-rempli par import des CP |
| IPID | Fiche européenne standardisée de 2 pages ; sans valeur contractuelle | Oui | Amorce de la taxonomie, repli si CG inaccessibles |
| Avenants | Modifications en cours de contrat | Non | Hors périmètre |

Beaucoup de garanties ne s'appliquent que si les CP les mentionnent. Exemple : chez AXA Belgium, la garantie vol n'existe que si les CP la mentionnent, et le contenu des annexes n'est couvert que si elles sont fermées par une serrure de sûreté. La bonne réponse est donc souvent « ça dépend de votre option et de tel fait ».

### Belgique et Luxembourg

|  | Belgique | Luxembourg |
| --- | --- | --- |
| Loi sur le contrat | Loi du 4 avril 2014 relative aux assurances | Loi modifiée du 27 juillet 1997 sur le contrat d'assurance |
| Superviseur | FSMA et BNB | Commissariat aux Assurances (CAA) |
| Assurance habitation obligatoire ? | Pour les locataires en Wallonie (depuis 2018) et en Flandre | Non |
| Catastrophes naturelles | Couverture légale imposée depuis 2006 | Garantie optionnelle (inondation) |
| RC vie privée | Produit séparé (RC familiale) | Souvent incluse dans la multirisque habitation |
| Marché | Plus fragmenté | 4 compagnies = 90 % du non-vie (Foyer, Lalux, AXA, Baloise) |

Conséquence : les contrats luxembourgeois sont plus hétérogènes et dépendent davantage des options, ce qui rend l'outil plus utile et le formulaire de CP plus important.

### Accès aux documents

- **Foyer** : CG accessibles seulement avec un numéro client et un numéro de police. Ne pas contourner ; IPID public, CG seulement si obtenues légalement.
- **Baloise Luxembourg** : CG sur demande ou sur baloise.lu ; IPID en ligne.
- **AXA Luxembourg** : documents produit en PDF sur axa.lu.
- **Lalux** : à vérifier.
- **Belgique** : CG généralement téléchargeables (Ethias, AXA, Belfius…) ; classement des 4 premiers et disponibilité à vérifier à la constitution du corpus.

Les CG sont versionnées : un contrat reste régi par l'édition en vigueur à sa souscription. Le manifeste enregistre pour chaque document l'URL source, l'empreinte SHA-256, la date de récupération et la référence d'édition imprimée dans le document. Aucune version n'est écrasée : l'app affiche la date d'édition utilisée et laisse choisir quand plusieurs éditions existent. L'utilisateur peut aussi importer une édition plus récente, traitée pour sa session uniquement. La surveillance automatique des mises à jour est une extension.

### Choix pour l'outil

- CG pré-ingérées pour le corpus, IPID en complément ; date d'édition affichée, choix de l'édition quand il y en a plusieurs.
- CP : formulaire simplifié (formule, options vol, inondation, jardin…, statut propriétaire ou locataire). L'utilisateur peut importer ses CP pour le pré-remplir, puis il valide ; seules les valeurs du formulaire entrent dans le pipeline et deviennent des faits cités comme les clauses.
- CG non publiées sur l'outil, ou plus récentes : import par l'utilisateur, traitées pour la session uniquement.
- Import complet des CP (scans, OCR, autres mises en page, usage direct) en extension.
- La loi luxembourgeoise de 1997 peut servir de source secondaire citable, séparée des clauses du contrat.

### Données personnelles et droits

- **CP importées** : l'outil devient responsable de traitement. Consentement explicite à l'import et notice d'information ; minimisation (seuls formule, options, montants, franchise et référence des CG sont extraits) ; masquage des données personnelles avant tout appel LLM (expressions régulières pour IBAN et numéros, détection des noms et adresses, par exemple avec Presidio) ; rien n'est conservé, ni fichier ni texte ; fournisseurs de LLM sans réutilisation des données et avec accord de traitement, ce qui exclut le plan gratuit de Mistral ; hébergement Streamlit aux États-Unis mentionné dans la notice.
- **CP d'exemple fictives**, marquées comme telles, pour les tests et la démo.
- **CG importées par l'utilisateur** : traitées pour la session uniquement, jamais mutualisées sans accord de l'assureur. Droit d'auteur et confidentialité s'y opposent ; l'exception de fouille de textes de la directive 2019/790 couvre l'analyse, pas la remise à disposition à d'autres.
- **CG publiques** : pas de PDF bruts dans le dépôt public ; seulement le manifeste, un script de téléchargement et les données extraites avec des citations courtes.
- Analyse non juridique, à faire valider avant toute mise en production.

## Architecture

L'approche retenue est l'extraction structurée hors ligne suivie d'un raisonnement condition par condition (approche D) : le LLM juge des conditions élémentaires, le code construit le verdict.

&#91;embedded content: architecture · ingestion hors ligne et pipeline en ligne\]

L'ingestion transforme chaque contrat en données structurées une seule fois ; à chaque question, le pipeline ne lit que les garanties candidates et leurs définitions, puis le code tranche.

### Approches écartées

| Approche | Principe | Pourquoi écartée |
| --- | --- | --- |
| A. Contexte long | Tout le contrat dans le prompt | Ne passe pas à l'échelle, citations non vérifiables, « lost in the middle ». Gardée comme **référence d'évaluation** |
| B. RAG classique | Découpage fixe + embeddings | Sépare une garantie de ses exclusions et définitions, gère mal les négations |
| C. RAG structurel | Découpage par sections | Mieux, mais le raisonnement reste implicite |
| E. Neuro-symbolique | Le LLM encode le contrat en Prolog | Trop ambitieux pour 24 h ; citée en perspective |

### Ingestion hors ligne (une fois par contrat)

1. **Parsing selon la structure** : PDF vers arbre de sections avec numéros de page et coordonnées (Docling, ou PyMuPDF en version légère).
2. **Extraction typée** des garanties, exclusions et définitions, chacune avec son texte source exact.
3. **Rattachement** de chaque garantie aux concepts de la taxonomie, avec score de confiance.
4. **Vérification** : chaque texte cité doit exister dans le document source.
5. **Stockage** dans le dépôt (JSON ou SQLite) et rapport d'ingestion (garanties non rattachées, citations invalides).

### Pipeline en ligne (à chaque question)

1. **Planification** : un appel structuré découpe le message en demandes typées (question de couverture, information sur le contrat, réponse à une clarification, hors périmètre). Chaque question de couverture correspond à un couple (événement, bien endommagé) et reçoit ses propres faits typés, faits communs recopiés. Les consignes de présentation sont extraites à part. Au plus 5 demandes par message.
2. **Répartition** : chaque question de couverture suit les étapes 3 à 6, isolée et en parallèle, avec ses propres garanties candidates.
3. **Sélection des garanties candidates** par filtre sur les concepts et les options des CP. Concept « autre » : recherche BM25 + embeddings sur toutes les clauses, garanties et exclusions.
4. **Évaluation** de chaque condition et exclusion : `remplie`, `non remplie`, `inconnue` ou `ambiguë`, avec l'identifiant de la clause. Les définitions du contrat sont injectées automatiquement.
5. **Agrégation déterministe en code** : `couvert`, `non couvert` ou `indéterminé`, avec faits manquants et clauses ambiguës.
6. **Vérification des citations** par programme.
7. **Composition** : assemblage des verdicts selon les consignes. Un tableau est rendu par un modèle de présentation, sans LLM ; la prose est rédigée par le LLM puis contrôlée (chaque verdict affiché doit égaler le verdict calculé). Les formats autorisés sont limités : aucune consigne ne supprime les citations ni ne change un « indéterminé ». Les parties hors périmètre sont listées explicitement.
8. **Clarification** : un état par demande ; chaque réponse de l'utilisateur est rattachée à la bonne demande, dont le verdict est recalculé.

Alternative écartée pour le prétraitement : un agent qui appelle à volonté un outil de vérification de couverture. Plus souple, mais coût, évaluation et fidélité des verdicts plus difficiles à garantir ; citée en perspective.

```latex
\text{couvert} = \bigvee_{g \in \text{candidates}} \Big( \bigwedge_{c \in g} c \Big) \;\wedge\; \neg \big(\exists\, \text{exclusion applicable}\big)
```

Une condition `inconnue` ou `ambiguë` qui pourrait changer le résultat rend le verdict `indéterminé`. Ne trouver aucune garantie ne vaut jamais « non couvert » sans clause explicite.

## Modèle de données et taxonomie

Le schéma reprend l'ordre de raisonnement d'un gestionnaire de sinistres : le cas entre-t-il dans une garantie, une exclusion l'en fait-elle sortir, et que signifient exactement les mots ? D'où trois types, chacun avec un rôle logique distinct dans le verdict.

### Les trois types

| Type | Rôle | Portée | Exemple |
| --- | --- | --- | --- |
| Garantie | Positif : événement, biens, lieux, conditions (ET) ; c'est à l'assuré d'y entrer | Une garantie, optionnelle ou non selon les CP | Vol (AXA BE) : seulement si mentionné en CP |
| Exclusion | Négatif : retire des cas couverts ; à invoquer par l'assureur, interprétation stricte | Générale ou propre à une garantie, avec exceptions | Brûlures sans incendie |
| Définition | Fixe le sens d'un terme dans tout le contrat ; ne vote pas | Transversale, propre au contrat | « Incendie », « effraction », « annexe » |

Compléments : conditions rangées sous leur garantie ; obligations de l'assuré notées comme conditions ; plafonds et franchises extraits pour l'affichage mais hors du verdict ; une **source** pour chaque élément (document, page, chemin de sections, texte exact, coordonnées).

```python
class Source(BaseModel):
    doc_id: str; page: int; section_path: list[str]; verbatim: str

class Condition(BaseModel):
    id: str; texte: str; termes_definis: list[str]; source: Source

class Garantie(BaseModel):
    id: str; nom_contrat: str; concepts: list[str]
    optionnelle_cp: bool; biens: list[str]; lieux: list[str]
    conditions: list[Condition]; source: Source

class Exclusion(BaseModel):
    id: str; portee: Literal["generale", "specifique"]
    garanties_visees: list[str]; exceptions: list[str]
    termes_definis: list[str]; source: Source

class Definition(BaseModel):
    terme: str; texte: str; source: Source
```

### La taxonomie : un pivot, pas un dictionnaire

Le sinistre est décrit avec les mots de l'utilisateur, chaque contrat avec les siens (« Vol », « Vol et vandalisme », « Soustraction frauduleuse »). Les concepts servent de langue commune pour **orienter**, jamais pour **définir**.

Ce qu'elle apporte : une sélection des garanties par filtre, fiable et explicable ; l'ajout d'un assureur sans toucher au pipeline en ligne ; un formulaire de CP générique ; la comparaison entre contrats ; une évaluation par concept.

**Un seul axe pour les concepts, celui des périls** (une quinzaine) : incendie et assimilés · tempête, grêle, neige · dégâts des eaux · catastrophes naturelles · bris de vitrage · vol et vandalisme · dommages électriques · heurt · attentats et conflits du travail · RC immeuble · RC vie privée · RC locative et recours des tiers · protection juridique · assistance · dommages accidentels.

**Des facettes séparées** : biens (bâtiment, contenu, objets de valeur, vélos, mobilier de jardin…), lieux (bâtiment, dépendances, parties communes, jardin, hors domicile), statut (propriétaire, locataire).

Pourquoi une quinzaine : trop peu de concepts ne filtrent rien, trop rendent le rattachement instable et invérifiable à la main. Une quinzaine correspond à la taille naturelle du domaine (les IPID listent une dizaine à une quinzaine de garanties).

### Cas limites

- **Même mot, sens différents** : les définitions ne sont jamais fusionnées. Un terme est toujours résolu dans le contrat analysé. Si A définit l'incendie par les flammes et B par les flammes et la chaleur, la bougie donne deux verdicts, chacun justifié.
- **Terme non défini par le contrat** : condition marquée `ambiguë`, le principe d'interprétation en faveur de l'assuré est mentionné sans être appliqué par l'outil.
- **Orientation : rappel ; évaluation : précision.** Plusieurs concepts peuvent être activés ; chaque garantie est évaluée strictement.
- **Question hors périmètre** (auto, santé) : réponse explicite, pas de tentative.
- **Question d'habitation sans concept** : concept « autre », recherche sur toutes les clauses (exclusions comprises), verdict marqué comme obtenu par recherche libre, question enregistrée.

### Faire évoluer la taxonomie

Fichier YAML versionné dans le dépôt : identifiant stable, libellé, description, exemples, notes « inclut / n'inclut pas » (c'est ce que lit le LLM pour rattacher).

1. À l'ingestion, toute garantie non rattachée va dans « autre », en quarantaine, listée dans le rapport. Elle reste utilisable via la recherche.
2. Les garanties en quarantaine et les questions non orientées sont regroupées ; un LLM propose de rattacher, créer ou scinder un concept.
3. Un humain décide ; la décision entre au journal des décisions.
4. Seules les garanties concernées sont rattachées de nouveau ; le jeu d'évaluation vérifie l'absence de régression.

Règles : un identifiant n'est jamais renommé ni réutilisé (dépréciation avec renvoi) ; un contrôle automatique vérifie que chaque garantie est rattachée ou explicitement relue.

## LLM et budget

Le budget total est plafonné à 20 € : ingestion en mode batch (50 % moins cher), fonctionnement en ligne plafonné, et clé API personnelle possible pour l'utilisateur.

### Estimation (à confirmer sur le premier contrat)

| Poste | Volume estimé | Coût estimé |
| --- | --- | --- |
| Ingestion, un passage complet | 1 à 1,5 M tokens en entrée, 300 k en sortie | \~4 $ (Sonnet 4.6 batch), \~1 $ (Haiku 4.5 batch), < 1 $ (Mistral Large batch) |
| Une question en ligne | 1 appel de planification, puis 3 à 6 appels par demande (15 à 25 k tokens en entrée, \~2 k en sortie) | 2 à 4 centimes par demande (Haiku 4.5), \~10× moins (Mistral Small) |

**Répartition** : 8 € ingestion (2 ou 3 passages + mise au point), 7 € en ligne, 5 € de marge. **Limite de dépense stricte** réglée dans la console du fournisseur.

### Mode batch : précautions

- Délai garanti de 24 h chez Anthropic comme chez Mistral, souvent plus court en pratique : un batch lancé tard peut ne pas revenir à temps.
- Mettre au point les prompts en synchrone sur un seul contrat, puis lancer le batch complet tôt ; garder un script de secours synchrone.
- Valider chaque sortie avec Pydantic à la réception ; repasser les sorties invalides en synchrone. Les requêtes en échec restent facturées.
- Version de modèle figée (pas d'alias « latest »), température 0.
- Cache de prompt (instructions, lexique) cumulable avec le batch chez Anthropic.

### Plafonds en ligne

L'IP seule ne suffit pas : elle est partagée (tout un bureau derrière une IP) et falsifiable (en-tête `X-Forwarded-For`).

1. Plafond par session.
2. Plafond par IP, généreux.
3. **Plafond global par jour, compté en coût estimé** : le vrai garde-fou, avec la limite côté fournisseur.

En plus : résultats pré-calculés pour les deux exemples sur chaque contrat ; cache sur l'empreinte (contrat, sinistre, CP) ; longueur de saisie limitée et `max_tokens` fixé. Plafond atteint : exemples pré-calculés et proposition de clé personnelle.

### Clé API de l'utilisateur

- **Jamais conservée** : mémoire de session uniquement ; jamais sur disque, dans l'URL, les journaux, les messages d'erreur (`client.showErrorDetails = false`) ni la clé de cache.
- **Transparence** : la clé transite par le serveur sans y être stockée, lien vers le code qui la gère ; conseiller une clé dédiée avec limite de dépense, révoquée après l'essai ; l'hébergeur est un tiers ; pas de données personnelles dans le sinistre.
- **Dépendances figées** avec fichier de verrouillage et empreintes : des versions piégées de LiteLLM ont volé des identifiants en mars 2026.
- **Validation** de la clé par un appel minimal, erreurs traduites, tentatives limitées.
- **Liste blanche** de modèles testés, chacun avec son score d'évaluation et son coût estimé par question.
- Limite de débit par session maintenue ; aucun point d'entrée générique vers le fournisseur.

### Couche d'abstraction

```python
class LLMClient(Protocol):
    def structured(self, messages: list[dict], schema: type[T], *, max_tokens: int) -> T: ...
```

- Implémentation sur **Instructor** : sorties Pydantic validées, réessais, Anthropic, OpenAI, Google, Mistral via un paramètre « fournisseur/modèle ».
- Le pipeline n'importe jamais un SDK de fournisseur directement.
- Le batch reste propre à un fournisseur, hors de cette couche.
- **Choix des modèles** : Sonnet 4.6 en batch pour l'ingestion (les erreurs d'extraction se propagent) ; modèle en ligne choisi sur le jeu d'évaluation entre Haiku 4.5 et Mistral Small.

**Données personnelles** : dès que l'import des CP est actif, seuls des fournisseurs qui ne réutilisent pas les données et proposent un accord de traitement sont utilisables (le plan gratuit de Mistral est exclu). Le masquage a lieu avant tout appel.

## Livrables et hébergement

Trois livrables, tous gratuits à héberger : l'app sur Streamlit Community Cloud, le code sur GitHub, la documentation sur GitHub Pages.

| Livrable | Hébergement | Contenu |
| --- | --- | --- |
| Application | Streamlit Community Cloud | Analyser un sinistre · Contrats (fiches extraites) · Évaluation · lien vers la doc |
| Dépôt public | GitHub | Code, manifeste et script de téléchargement des CG (sans PDF bruts), données extraites, CP d'exemple fictives, taxonomie YAML, jeu d'évaluation, README court, `CLAUDE.md` |
| Site de documentation | GitHub Pages | Page sur mesure « façon artefact », schémas, évaluation |

### Streamlit : limites et parades

| Limite | Conséquence | Parade |
| --- | --- | --- |
| Script réexécuté à chaque interaction | État à gérer explicitement | `st.session_state`, cache des opérations coûteuses |
| Mise en forme limitée | Pas de design sur mesure | Thème configuré, peu de CSS |
| Pas de visionneuse PDF avec surlignage | Citation moins parlante | Image de la page générée par PyMuPDF avec rectangle de surbrillance, dans un popover |
| Environ 0,08 à 2 cœurs, 0,7 à 2,7 Go de RAM | Docling ne tourne pas en ligne | Tout parser hors ligne ; PyMuPDF pour un éventuel import utilisateur |
| Système de fichiers éphémère | Compteurs, cache, imports perdus au redémarrage | Acceptable pour une démo ; mentionné dans les limites |
| Veille après 12 h sans trafic | Premier visiteur attend le réveil | Réveiller l'app avant d'envoyer le lien |

Secrets via `st.secrets`. Chat natif (`st.chat_message`, `st.chat_input`), multipage, `st.status` pour l'affichage progressif.

### Site de documentation

Page statique sur mesure (HTML, Tailwind, schémas SVG ou Mermaid, graphiques Chart.js ou Observable Plot). La mise en page est séparée des données pour rester à jour :

- le texte est mis à jour par l'agent de code à chaque fonctionnalité (règle dans `CLAUDE.md`) ;
- les chiffres et exemples sont lus depuis des JSON produits par le code : résultats d'évaluation, taxonomie, corpus, traces réelles des deux exemples ;
- une GitHub Action recopie ces fichiers et redéploie à chaque push sur `main` ;
- chaque bloc chiffré affiche date, commit et modèle du dernier passage.

**Plan de la page** :

1. En-tête : le problème en une phrase, lien vers l'app, capture animée.
2. Pourquoi l'approche naïve échoue.
3. Comprendre l'assurance en 2 minutes (CG, CP, IPID, Belgique et Luxembourg).
4. Architecture (schéma ingestion + pipeline).
5. Modèle de données et formule d'agrégation.
6. Taxonomie : carte des concepts, garanties rattachées par assureur.
7. Pas à pas sur le vélo et la bougie, idéalement un même sinistre avec deux verdicts.
8. Évaluation.
9. Choix et alternatives (journal des décisions).
10. Limites et perspectives.
11. Coûts.

Alternative si l'écriture en Markdown est préférée : Quarto (Python exécuté à la construction, Mermaid), plus simple mais moins libre visuellement.

## Évaluation

Un jeu de 20 à 30 cas annotés à la main sur au moins 3 contrats (dont les deux exemples de l'énoncé), comparé à une référence « contexte long ». Il n'existe pas de benchmark public pour cette tâche : l'évaluation reste locale, comme le recommande l'article fourni.

**Contenu d'un cas** : contrat, description du sinistre, CP simulées, verdict attendu (`couvert`, `non couvert`, `indéterminé`), clauses attendues, faits manquants attendus. Inclure volontairement des cas ambigus, des cas hors périmètre et un même sinistre sur deux contrats aux définitions différentes.

**Messages composés** : quelques cas regroupent plusieurs sinistres, mélangent une partie hors périmètre ou imposent un format (tableau). Ils mesurent la qualité du découpage : demandes trouvées, faits attribués à la bonne demande, consignes respectées sans altérer les verdicts.

| Métrique | Ce qu'elle mesure | Calcul |
| --- | --- | --- |
| Justesse du verdict | Verdict correct | Comparaison à l'annotation |
| Faux « couvert » | Erreur la plus coûteuse pour l'assureur | Comptée séparément |
| Faux « non couvert » | Erreur la plus coûteuse pour l'assuré | Comptée séparément |
| Qualité de l'abstention | `indéterminé` quand il le faut, et seulement là | Précision et rappel sur les cas ambigus |
| Citations valides | Texte cité présent dans la source | Automatique |
| Citations pertinentes | Les bonnes clauses sont citées | Recouvrement avec l'annotation |
| Coût et latence | Prix et temps par question | Mesuré par modèle |

**Comparaisons** : approche D contre référence A (contexte long) ; modèles en ligne entre eux (Haiku 4.5, Mistral Small, autres de la liste blanche) sur un graphique coût / qualité.

**Production** : un script `eval` écrit `eval/results.json` (avec date, commit, modèle), lu par l'app et par le site de documentation.

## Objectifs incrémentaux

Le projet avance par objectifs ordonnés, du socle nécessaire aux extensions. Après chaque objectif, il existe une version déployée et présentable : on peut s'arrêter à tout moment avec quelque chose à montrer.

**Définition commune de « terminé »** : le code est poussé, l'app déployée fonctionne, la documentation est à jour, une entrée est ajoutée au journal des décisions si un choix a été fait.

### Palier 0 – Fondations (nécessaire)

1. **Squelette déployé.** Dépôt public structuré (`src/`, `data/`, `eval/`, `site/`), dépendances verrouillées, `CLAUDE.md` avec les règles du projet (mise à jour de la doc, journal des décisions, aucune clé dans les journaux), app Streamlit minimale en ligne, secrets configurés.
   - Terminé quand l'URL publique répond.
2. **Premier contrat.** Un jeu de CG téléchargé, décrit dans un manifeste (pays, assureur, produit, référence et date d'édition, URL source, empreinte SHA-256, date de récupération) ; PDF bruts hors du dépôt public, script de téléchargement.
3. **Parsing structurel.** PDF vers arbre de sections JSON avec pages et coordonnées.
   - Terminé quand l'arbre du premier contrat est relu et correct.

### Palier 1 – Chaîne complète sur un contrat (nécessaire)

4. **Couche LLM.** Interface `LLMClient` sur Instructor, un fournisseur, configuration par variables.
5. **Schéma et taxonomie v1.** Modèles Pydantic ; taxonomie YAML (périls, facettes, descriptions « inclut / n'inclut pas »).
6. **Extraction du premier contrat** en synchrone : garanties, exclusions, définitions, rattachement aux concepts, vérification des citations, rapport d'ingestion.
   - Terminé quand chaque citation est vérifiée ou signalée.
7. **Pipeline en ligne minimal.** Analyse du sinistre, garanties candidates, évaluation des conditions et exclusions, agrégation déterministe, verdict cité.
   - Terminé quand les deux exemples de l'énoncé obtiennent un verdict justifié (ou un « indéterminé » argumenté) en ligne de commande.
8. **App v1.** Choix du contrat, saisie du sinistre, verdict, raisonnement dépliable, clauses citées avec page.
   - Premier livrable démontrable.
9. **Documentation v1.** Site GitHub Pages avec le problème, l'architecture et les choix ; GitHub Action de déploiement en place.

### Palier 2 – Honnêteté et robustesse (attendu)

10. **Planificateur** : le message devient une liste de demandes typées (couverture, information sur le contrat, réponse à une clarification, hors périmètre), avec des faits propres à chaque couple (événement, bien) et des consignes de présentation ; au plus 5 demandes.
11. **Répartition et composition** : un pipeline isolé par demande, en parallèle ; tableau rendu sans LLM, prose contrôlée ; formats autorisés limités ; parties hors périmètre listées.
12. **Formulaire de CP simplifiées**, généré depuis la taxonomie ; les réponses deviennent des faits cités.
13. **Import des CP comme raccourci** : extraction du texte, masquage des données personnelles, formulaire pré-rempli à valider, fichier oublié ; consentement et notice d'information ; CP d'exemple fictives pour les tests et la démo.
14. **Boucle de clarification** : un état par demande, questions sur les faits manquants, verdict recalculé après réponse.
15. **Cas limites** : concept « autre » avec recherche sur toutes les clauses ; aucun résultat = `indéterminé` ; terme non défini = `ambiguë`.
16. **Garde-fous de coût** : plafonds par session, par IP et global ; `max_tokens` ; longueur de saisie ; cache ; résultats pré-calculés des exemples ; limite côté fournisseur.

### Palier 3 – Passage à l'échelle du corpus (attendu)

17. **Corpus complet** : 4 assureurs au Luxembourg, 4 en Belgique (dont Foyer Belgium), CG ou IPID selon l'accès, manifeste à jour.
18. **Ingestion en batch** après mise au point synchrone ; validation à la réception, reprise des sorties invalides.
    - Terminé quand les 8 fiches et le rapport d'ingestion sont produits.
19. **Page « Contrats »** : fiche structurée par contrat (garanties, concepts, exclusions, définitions, confiance, date d'édition).
20. **Choix de l'édition des CG** : date d'édition affichée à chaque verdict, sélection quand plusieurs éditions existent, présélection si la référence est lue dans les CP importées.
21. **Comparaison entre contrats** : même sinistre, verdicts côte à côte.

### Palier 4 – Évaluation et documentation complète (attendu)

22. **Jeu d'évaluation** de 20 à 30 cas annotés, dont des messages composés, et script `eval` produisant `eval/results.json`.
23. **Référence et comparaison de modèles** : approche D contre contexte long ; Haiku 4.5 contre Mistral Small ; choix du modèle en ligne justifié par les chiffres.
24. **Documentation complète** : les 11 parties du plan, données JSON branchées, traces réelles du vélo et de la bougie, graphiques d'évaluation.

### Palier 5 – Extensions (non nécessaires, par intérêt décroissant)

25. **Clé API de l'utilisateur** : saisie, validation, liste blanche de modèles avec score et coût, toutes les précautions listées plus haut.
26. **Import de CG par l'utilisateur** (non publiées sur l'outil ou plus récentes) : PyMuPDF et extraction à la volée, sous plafond de coût, traitement pour la session uniquement.
27. **Clause surlignée** dans l'image de la page PDF.
28. **Questions multilingues** (allemand, anglais) sur des contrats en français.
29. **Import complet des CP** : scans et OCR, mises en page variées, usage direct sans passer par le formulaire.
30. **Outil de mise à jour de la taxonomie** : regroupement des « autre », propositions par LLM, revue en ligne de commande.
31. **Lois comme source secondaire** (loi luxembourgeoise de 1997, loi belge de 2014), citées séparément des clauses.
32. **Plafonds et franchises** : estimation du montant indemnisable.
33. **Surveillance automatique des CG** : GitHub Action planifiée, comparaison d'empreintes, détection de nouveaux liens sur les pages produit, différence structurée, réingestion après validation.
34. **Prototype neuro-symbolique** : encodage d'un contrat en logique, comparé à l'approche D.

## Risques et points ouverts

| Risque | Effet | Parade |
| --- | --- | --- |
| Batch trop lent | Corpus non ingéré à temps | Lancer tôt ; script synchrone de secours |
| CG inaccessibles (Foyer, peut-être Lalux) | Corpus incomplet au Luxembourg | IPID en repli ; import par l'utilisateur pour sa session ; limite documentée |
| Extraction de mauvaise qualité | Erreurs propagées à tous les verdicts | Modèle fort pour l'ingestion, vérification des citations, relecture via la page « Contrats » |
| Mauvais découpage d'un message | Faits mélangés entre sinistres, demande oubliée | Unité (événement, bien), messages composés dans l'évaluation, demandes affichées à l'utilisateur |
| Données personnelles dans les CP importées | Manquement au RGPD | Masquage avant appel, rien conservé, consentement et notice, fournisseurs sans réutilisation |
| Redistribution de CG protégées | Atteinte au droit d'auteur ou à la confidentialité | Pas de PDF bruts publiés, CG importées limitées à la session |
| Dépassement de budget | Coût au-delà de 20 € | Limite côté fournisseur, plafond global, résultats pré-calculés |
| App en veille au moment de la démo | Mauvaise première impression | Réveiller avant l'envoi du lien |
| Fuite d'une clé utilisateur | Atteinte à la confiance | Précautions de la section LLM ; extension seulement si le reste est solide |

**Points ouverts**

- [ ] Confirmer le classement des 4 premiers assureurs habitation en Belgique et la place de Foyer Belgium.
- [ ] Vérifier la disponibilité des CG chez Lalux, AXA Luxembourg et Baloise, et leurs langues de publication.
- [ ] Compter les tokens réels sur le premier contrat et ajuster l'estimation de budget.
- [ ] Confirmer l'échéance exacte et le format de restitution (présentation orale ou non).

## Sources

- [Parse the folder, not just the PDFs](https://towardsdatascience.com/parse-the-folder-not-just-the-pdfs-the-relational-tables-rag-needs-on-a-case-file/) – ressource du recruteur
- [Towards Robust Legal Reasoning: Harnessing Logical LLMs in Law](https://arxiv.org/pdf/2502.17638) – arXiv, 2025
- [CovrLogic](https://coverager.com/covrlogic-wants-to-automate-insurance-coverage-decisions/) – Coverager
- [CLAUSE – every decision, cited](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii/team-lucilius/clause-every-decision-cited) – lablab.ai
- [AXA Belgium – CG Confort Habitation Flex Vol](https://www.axa.be/axa-documents/ibp/000039-4185790-20170501.pdf)
- [Ethias – CG Assurance Habitation](https://www.ethias.be/content/dam/B2C/general/pdf/general-conditions/cg-habitation-fr.pdf)
- [Belfius – IPID assurance locataire](https://www.belfius.be/common/FR/multimedia/MMDownloadableFile/Insurance/IPID/IPID-huurderverzekering.pdf)
- [CAA – Loi du 27 juillet 1997, version coordonnée](https://www.caa.lu/uploads/documents/files/Loi_ContratAssurance_1997-07-27_coord_2025-11-25.pdf)
- [Paperjam – Pourquoi le marché non-vie luxembourgeois reste fermé](https://paperjam.lu/article/pourquoi-le-marche-non-vie-luxembourgeois-reste-ferme)
- [Paperjam – L'assurance climatique](https://paperjam.lu/article/lassurance-climatique-une-preoccupation-croissante)
- [Chambre des Députés – Question sur les catastrophes naturelles](https://wdocs-pub.chd.lu/docs/exped/0131/143/263438.pdf)
- [Test-Achats – Assurer votre habitation](https://www.test-achats.be/argent/assurances/dossier/assurer-votre-habitation-un-must)
- [Foyer – Accès aux conditions générales](https://222.foyer.lu/en/general-conditions-help)
- [Baloise – IPID Home](https://www.baloise.lu/dam/baloise-lu/1890/particulier/documents/fiches/fiche-ipid/fr/ipid-home-fr-lu)
- [AXA Luxembourg – IPID Multirisques Habitation](https://axa.lu/sites/axa/files/cgv/Wroc_BIAAPGZUxBi.pdf)
- [Anthropic – Message Batches](https://platform.claude.com/docs/en/build-with-claude/message-batches)
- [Developers Digest – Mistral cost levers](https://www.developersdigest.tech/models/cost-levers/mistral)
- [Arthur.ai – LiteLLM supply chain attack](https://www.arthur.ai/column/litellm-supply-chain-attack-pypi-compromise-2026)
- [Instructor](https://python.useinstructor.com)
- [SnapDeploy – State of Free Hosting 2026](https://snapdeploy.dev/state-of-free-hosting)
- [Hugging Face – Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview)
