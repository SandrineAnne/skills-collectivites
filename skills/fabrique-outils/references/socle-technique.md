# Socle technique

Sommaire : 1. Structure du projet · 2. Code · 3. Sécurité et RGPD · 4. Authentification (décision en attente) · 5. Spécificités par format · 6. Scalabilité, pérennité, fin de vie · 7. Tests et analyses · 8. Correspondance avec la grille de vigilance

Tout ce qui suit est décidé et appliqué par Claude : l'agent n'a pas à le connaître (voir `dialogue-agent.md`). Les pratiques de code et ce que `fabriquer.py` refuse ou signale sont dans `pratiques-de-code.md`. Le projet se crée avec `scripts/creer_projet.py` et se contrôle avec `build/fabriquer.py` (voir `paquet-integration.md`).

## 1. Structure du projet

Dans Cowork, un sous-dossier par application dans le dossier de travail :

```
<nom-appli>/
├── README.md              fiche d'identité + démarrage en 5 minutes
├── SPEC.md                la référence : règles de gestion RG-xx
├── CHANGELOG.md           une entrée par version livrée (Ajouté / Modifié / Corrigé, en langage métier)
├── VERSION                ex. 1.2.0 — seule source du numéro de version
├── reseau-autorise.txt    hôtes externes autorisés (vide par défaut) et leur raison
├── src/                   code (src/coeur/ = règles métier, sans interface) ; constante APP_VERSION déclarée une fois
├── tests/                 jeu de données fictives + résultats attendus
├── docs/                  grille-vigilance, recette, fiche-dsi, composants, decisions, derogations, perimetre, partage, incidents, exploitation, dokuwiki/
├── deploy/                (format B) compose.yaml, .env.exemple, vhost, playbooks, procédure d'installation
├── build/fabriquer.py     contrôle et fabrication du paquet
└── .gitignore             exclut .env, données réelles, fichiers de travail
```

## 2. Code

- Lisible par un agent qui ne l'a pas écrit : noms et commentaires en français, avec les mots de la SPEC ; fonctions courtes (moins de 80 lignes, un seul rôle) ; commentaires qui disent le pourquoi ; chaque règle métier repérée par son identifiant (`// RG-07 : …`).
- **Cœur pur :** `src/coeur/` ne lit aucun fichier, n'appelle aucun réseau, n'affiche rien ; l'interface et les lectures de fichiers l'appellent. C'est ce qui rend les règles testables en une seconde.
- **Aucune erreur avalée :** jamais de `except:` sans type ; une erreur ignorée volontairement porte un commentaire qui dit pourquoi.
- **Jamais de code exécuté à partir d'un texte** (`eval`, `exec`, `new Function`), ni de commande système construite avec une valeur reçue (`shell=True`, `os.system`).
- Dépendances minimales et justifiées dans le README ; versions figées (`requirements.txt` avec `==`, idéalement avec empreintes `--require-hashes` ; `package-lock.json` et `npm ci` ; images avec une version précise, jamais `latest`). Délai de carence : ne pas adopter une version publiée depuis moins de 14 jours.
- Aucune ressource chargée depuis Internet à l'exécution, sauf les hôtes déclarés dans `reseau-autorise.txt` avec leur raison (exemple : tuiles d'un fond de carte). Bibliothèques embarquées (format A) ou installées dans l'image (format B).
- Messages d'erreur compréhensibles (« Le fichier ne contient pas de colonne Montant »), jamais de trace technique à l'écran ; le détail va dans le journal technique.
- Paramètres (listes, seuils, libellés, périmètres) dans un fichier de configuration, pas en dur : l'outil devient réutilisable par une autre direction sans recoder.
- **Retour visible à chaque action :** toute copie dans le presse-papiers, tout téléchargement, toute sauvegarde affiche une confirmation claire (ce qui s'est passé, où le trouver) et, en cas d'échec, un message qui propose une autre voie (par exemple le fichier à la place de la copie).
- **Rôle d'éditeur** (`role-editeur.md`) : chaque fichier reçu décrit dans `docs/entrees.md` avec un exemple inventé ; mention « Produit avec … » sur tout document produit ; questions-tests et mode de secours pour toute fonction d'IA ; lien « Signaler un problème » ; briques communes plutôt que du code recopié.
- **Travail sur copie :** ne jamais écraser un fichier fourni par l'agent ou un collègue ; le copier dans le dossier du projet et travailler sur la copie.
- Format de code : linter et formateur de la langue quand ils existent (`ruff` pour Python, `eslint` pour JavaScript) ; types ou JSDoc sur les fonctions du cœur métier.
- Accessibilité de base : contrastes de la charte, navigation au clavier, interface utilisable sur petit écran si un usage mobile est prévu.
- Impression : feuille `@media print` dédiée, sans boutons ni éléments d'interface.

## 3. Sécurité et RGPD

- **Minimisation :** ne traiter que les données utiles ; refuser à l'import les colonnes nominatives dont l'outil n'a pas besoin ; aucune télémétrie, aucun envoi hors de la collectivité.
- **Secrets :** jamais dans le code, le compose ni le dépôt. Fichier `.env` sur le serveur (droits 600), exclu par `.gitignore` et des archives ; `.env.exemple` livré avec des valeurs factices. Un secret qui a circulé (capture, conversation, journal) est renouvelé, et renouvelé aussi à chaque départ du chef de projet, du référent ou du suppléant.
- **Entrées non fiables :** tout fichier reçu est suspect.
  - Taille maximale, type vérifié par le contenu (pas seulement l'extension), nom de fichier nettoyé (pas de chemin), archives limitées en taille décompressée, fichiers temporaires effacés après traitement.
  - XML lu sans entités externes (`defusedxml` en Python) ; requêtes SQL toujours paramétrées ; jamais de commande système construite avec une valeur saisie.
  - Rien d'importé (Excel, CSV, XML, saisie) n'est inséré tel quel dans une page : texte inséré avec `textContent`, jamais `innerHTML`.
  - **Exports tableur :** toute cellule qui commence par `=`, `+`, `-` ou `@` est neutralisée (apostrophe ou espace devant) pour éviter l'exécution de formules.
- **Réseau :** interne par défaut ; frontal HTTPS du serveur, conteneur jamais joignable en direct (valeurs concrètes : `environnement-collectivite.md`). Ouverture à l'extérieur : `ouverture-externe.md`.
- **Appels sortants :** aucun, hors la liste de `reseau-autorise.txt`. Jamais d'appel à l'API Anthropic (règle par défaut, à adapter dans `environnement-collectivite.md`).
- **Composants maintenus :** chaque composant (langage, bibliothèque, image, base) figure dans `docs/composants.md` avec sa **date de fin de support, vérifiée au jalon 3 sur le site de l'éditeur**. Un composant déjà sans support n'est pas livré ; un support qui se termine dans moins de 6 mois est signalé à la livraison. Cette règle complète la grille de vigilance sans en modifier le contenu.
- **Journal applicatif :** qui, quoi, quand (horodatage en UTC), sans contenu sensible dans le journal ; durée de conservation à fixer avec le DPO ; rotation prévue ; accès restreint.
- **Données personnelles ou sensibles :** avis du DPO avant toute donnée réelle (point de la grille sur l’avis du DPO) ; fiche de traitement si nécessaire.
- **Décisions sur des personnes :** un outil qui classe, note ou trie des personnes (candidats, bénéficiaires, agents) prépare une décision (point bloquant de la grille) : avis du DPO avant de le construire, et l'outil présente toujours ses résultats comme des propositions que l'agent vérifie.
- **Exceptions :** toute règle mise de côté (compte partagé, mise en service avant avis…) est notée dans `docs/derogations.md` (règle, ce qui est fait à la place, raison, décideur par fonction, date, date de revue, avis demandé). Une exception non notée n'existe pas ; une exception notée est visible de la cybersécurité et de la DSI.
- **Diffusion hors de la collectivité (réseaux sociaux, partage public) :** version dédiée, sans donnée, secret ni nom de serveur interne, après accord de la cellule ; l'outil en service n'est jamais hébergé hors du SI (point de la grille sur l'hébergement). Cas détaillés : `ouverture-externe.md`.

### Données réelles de personnes : ce que le contrôle arrête

Aucune donnée réelle n'entre dans le dossier d'un outil : ni dans les exemples, ni dans les tests, ni dans la documentation. Le contrôle cherche les **numéros de sécurité sociale et les IBAN dont la clé est juste** : une clé juste signale presque toujours une donnée réelle. C'est une règle du socle de sûreté : elle bloque aussi un brouillon. La valeur n'est jamais recopiée dans le bilan (quatre premiers caractères seulement).

- Un exemple inventé : changer un chiffre suffit, la clé devient fausse.
- Un outil qui a besoin d'exemples à clé juste (contrôle de RIB, par exemple) les déclare, un par ligne, dans `tests/donnees/exemples-fictifs.txt` : ils sont acceptés, leur nombre figure au bilan, et le référent confirme qu'ils sont inventés.
- Les noms, adresses et dates de naissance ne se détectent pas automatiquement : la règle reste la même, et Claude ne demande jamais de fichier réel.

### Ce que le contrôle lit, et ce qu'il ne garantit pas

`fabriquer.py` lit **tout ce qui partirait dans le paquet**, quels que soient l'extension, l'encodage, le dossier ou la longueur des lignes. Ce qu'il ne peut pas lire (image, document, programme compilé, archive) est nommé dans le bilan : rien n'est sauté en silence.

- **Adresses :** toute adresse écrite dans le code doit être déclarée, qu'elle soit dans l'appel, dans une constante ou dans un fichier de réglages. Une adresse construite à l'exécution (`'https://' + hôte`) est refusée : le contrôle ne peut pas en vérifier la destination.
- **Format A :** la balise de sécurité (CSP) est obligatoire dès qu'un paquet est fabriqué. C'est la seule protection qui porte sur l'exécution réelle : le navigateur bloque lui-même tout appel hors liste, et refuse `eval()` même déguisé tant que la balise ne contient pas `'unsafe-eval'`.
- **Format B :** le code du serveur peut appeler une adresse calculée ou reçue, que la lecture ne voit pas. Demander à la DSI de limiter les sorties du serveur aux hôtes de `reseau-autorise.txt`.
- **Exemptions :** toujours motivées, toujours recopiées au bilan.
- **Lignes très longues :** une bibliothèque embarquée contient souvent ce que le contrôle refuse ailleurs. Ce qu'il y trouve donne une alerte, à rapprocher de `docs/composants.md`.

Ce contrôle cherche des défauts connus ; il ne prouve pas leur absence. Un code qui cache ce qu'il fait peut lui échapper : il ne remplace ni la relecture, ni l'avis de la cybersécurité pour un outil sensible. Avant une installation, la cellule relance le contrôle **avec la copie de la skill** (`python3 <skill>/scripts/fabriquer.py <projet>`), et non avec celle du projet : l'empreinte du script figure en tête du bilan.

Les contournements connus sont rejoués par `scripts/autotest_surete.py` : un contournement signalé y devient un essai.

### Lecture de fichiers XML reçus

Un fichier XML reçu se lit sans entités externes : `XMLParser(resolve_entities=False, no_network=True)` avec lxml, ou la bibliothèque `defusedxml`. Le contrôle le rappelle quand il voit une lecture XML sans analyseur réglé.

## 4. Authentification — décision en attente

Le mode standard n'est pas encore arrêté (voir `decisions-a-prendre.md`). En attendant :

- règles fixes : comptes nominatifs, aucun compte générique (sinon exception notée), mots de passe hachés (argon2 ou bcrypt) si l'application en stocke, journal relié à l'identité ;
- sessions : cookies `HttpOnly`, `Secure`, `SameSite`, durée limitée, protection contre les envois forcés (CSRF) pour les actions qui modifient des données ; limitation des tentatives de connexion ;
- concevoir l'application pour que l'authentification soit remplaçable : l'identité de l'utilisateur est lue à un seul endroit du code ;
- présenter les options à la cellule avec leur effet sur la grille :

| Option | Atouts | Effet sur la grille |
|---|---|---|
| Annuaire AD en LDAPS | Comptes nominatifs, désactivés automatiquement au départ de l'agent ; aucun mot de passe à gérer | Compte dans la grille (connexion à l'annuaire) |
| Portail d'authentification en frontal (par exemple Authelia) | Application déchargée de l'authentification ; un portail commun possible pour toutes les applis d'un serveur | Base de comptes propre : mots de passe à gérer (grille) ; adossé à l'annuaire : connexion à l'annuaire (grille) |
| Comptes locaux dans l'application | Simple à démarrer | À éviter : gestion des mots de passe et traçabilité à coder soi-même (deux points de la grille) |

## 5. Spécificités par format

### A. HTML autonome

- Un seul fichier, bibliothèques embarquées. Aucun appel réseau, sauf hôtes déclarés dans `reseau-autorise.txt` (c'est vérifié par `fabriquer.py` et par le test navigateur qui bloque toute requête externe). Dans le fichier, une balise de politique de sécurité (`Content-Security-Policy`) limite les connexions aux hôtes déclarés.
- Le stockage du navigateur n'est qu'un confort : export et import d'un fichier de sauvegarde (JSON) et témoin visible « sauvegardé dans un fichier / pas encore ». Le fichier de sauvegarde porte le nom de l'outil et sa version ; un fichier d'un autre outil est refusé, un fichier d'une version antérieure du même outil est converti.
- **Aucune donnée de personne n'est conservée dans le stockage du navigateur** ; un bouton « Tout effacer » vide les saisies.
- **Péremption :** un fichier diffusé par courriel vieillit sans qu'on s'en aperçoive ; l'outil affiche sa date de version et un lien vers la dernière version, et un message discret au-delà de 6 mois.
- **Cartes :** les tuiles du fond de carte sont le seul appel externe usuel ; les déclarer (hôte et raison) et n'y envoyer aucune donnée de l'agent.

**Un outil local ne se met pas à jour tout seul.** Trois gestes le rendent entretenable : un seul lieu de téléchargement, indiqué dans le README ; la date de la version donnée au module de prise en main (`dateVersion`), qui affiche après six mois « vérifiez qu'il n'existe pas une version plus récente » ; et, si l'outil garde des saisies dans le navigateur, des boutons « Exporter » et « Importer » (le contrôle le signale s'ils manquent).

### B. Web conteneurisé

Principes, valables quel que soit le serveur ; les valeurs concrètes de votre collectivité (par exemple podman compose, dossiers, nginx, `restart: always`, supervision) sont dans `environnement-collectivite.md`, section « Hébergement » ; le gabarit `deploy/compose.yaml` les applique :

- images officielles à version précise (idéalement figées par empreinte `@sha256`), jamais `latest` ; `healthcheck` ; limite mémoire ;
- **durcissement par défaut** : `read_only: true` avec `tmpfs` pour `/tmp`, `cap_drop: ALL`, `no-new-privileges`, utilisateur non root. Chacun peut être retiré **à condition de le noter dans `docs/derogations.md`** ;
- redémarrage automatique après un redémarrage du serveur (`restart: always`) ;
- conteneur joignable seulement par le frontal HTTPS du serveur (port publié sur `127.0.0.1`), accès restreint au réseau interne sauf ouverture déclarée ;
- vhost : en-têtes `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`, taille maximale des dépôts adaptée ;
- application sans état ; données dans une base (SQLite pour un petit volume, PostgreSQL au-delà) ou un volume, sous un dossier dédié à l'application ;
- **sauvegarde et restauration** : le dossier des données est sauvegardé par la supervision ; **la restauration est essayée avant la mise en service et la date de l'essai est notée** dans la fiche DSI ;
- avant chaque mise à jour, conserver l'image en service sous une étiquette de retour arrière (`avant-maj`) ;
- inscription dans la supervision des conteneurs et mise à jour du schéma d'infrastructure ;
- l'application expose une **adresse de santé** (`/sante`) qui répond 200 et donne sa version ; ses journaux vont sur la sortie standard ;
- image construite sur place : `Dockerfile` à partir de `deploy/Dockerfile.exemple` (image de base figée, dépendances avec empreintes, utilisateur non root) ;
- déploiement par `playbook_deploy.yaml` (Semaphore), contrôle par `playbook_check.yaml`, sur un serveur Podman ou Docker (variable `moteur`).

### C. Bureau (MSI)

- Exécutable, signature, antivirus : voir `environnement-collectivite.md`, section « Postes Windows » (jamais PS2EXE).
- Dépendances optionnelles (OCR, modèle de langue) détectées au démarrage ; si elles manquent, message clair et mode dégradé annoncé, jamais silencieux.
- Numéro de version visible, procédure de remplacement du MSI documentée.

### D. Grist

- Un document par besoin dans l'espace de travail du service ; colonnes et formules décrites dans la SPEC ; widgets personnalisés versionnés comme du code.

## 6. Scalabilité, pérennité, fin de vie

- Dimensionner sur la volumétrie à 2 ans de la SPEC ; tester avec un jeu fictif dix fois plus gros (temps de chargement, mémoire, lisibilité de l'écran).
- Dès que plusieurs agents partagent des données : format B, base côté serveur ; migrations du schéma numérotées et rejouables sans danger.
- Réversibilité : export ouvert (CSV, XLSX, JSON) de toutes les données saisies.
- Aucune dépendance à un poste ou à une personne : tout ce qu'il faut pour reconstruire est dans le dépôt.
- **Plusieurs outils qui partagent du code** (famille d'outils) : le code commun vit à un seul endroit, versionné ; avant de le modifier, reconstruire chaque outil et comparer le résultat avec la version précédente pour vérifier qu'aucun autre outil n'a bougé.
- **Revue du gain :** à 3 mois, mesurer l'indicateur de la SPEC (temps gagné, erreurs évitées) et le noter dans le CHANGELOG ; décider de garder, faire évoluer ou arrêter.
- **Fin de vie :** archiver le code et la documentation, effacer les données selon la durée convenue avec le DPO, retirer l'adresse, le vhost et l'inscription dans la supervision, mettre à jour le schéma d'infrastructure (voir `docs/exploitation.md`).

## 7. Tests et analyses

- Au moins un test par RG, sur données fictives, avec résultats attendus écrits à l'avance (`tests/`), et l'identifiant de la règle dans le test. Les tests sont des fonctions `test_…` dans des fichiers `test_*.py` (ou `*.test.js`, `test_*.js`, `essai_*.js`) : **`fabriquer.py` les exécute et refuse la livraison s'ils échouent** (pytest s'il est installé, sinon un lanceur intégré ; `node` pour JavaScript).
- Tests rapides et déterministes : pas de réseau, pas de date du jour, pas d'aléa. **Un défaut corrigé = un test ajouté.**
- **Rapprochements chiffrés :** pour tout outil qui affiche des montants ou des effectifs repris d'un fichier, les totaux sont comparés à la source, au centime près (calculs en nombres entiers de centimes), par une vérification indépendante du code de l'outil. Les fichiers Excel sources sont inspectés pour les lignes ou colonnes masquées et les filtres actifs avant de se fier aux totaux visibles.
- **Non-régression :** quand plusieurs outils partagent du code, reconstruction puis comparaison avec la version précédente.
- **Tests de sécurité :** fichier vide, fichier énorme, fichier malformé, nom de fichier piégé, cellule commençant par `=`, saisie contenant du HTML.
- Parcours automatisé dans un navigateur sans écran (Playwright) : parcours principal, écran de 390 px, zéro erreur dans la console, **zéro requête vers l'extérieur** (hors hôtes déclarés) ; tutoriel contrôlé par `scripts/test_prise_en_main.py` ; captures d'écran relues avant livraison. Si l'environnement ne permet pas de le faire, le dire.
- Format B : démarrage du compose, contrôle de santé, réponse derrière le frontal HTTPS, redémarrage du conteneur sans perte de données ; `playbook_check.yaml`.
- Le code étant généré par l'IA (point de la grille sur le code non relu), `fabriquer.py` lance lui-même les analyses dont les outils sont installés : `ruff` (erreurs bloquantes, conseils en alerte), `bandit` (gravité moyenne ou haute bloquante), `pip-audit` et `npm audit` (failles connues bloquantes), `gitleaks`, `trivy` sur demande (`--analyser-images`). Sans outil, il contrôle tout de même la syntaxe, les motifs dangereux, les secrets et les dépendances, et écrit ce qui n'a pas été testé. **Pour un outil orange : `--exiger-analyses`.** Résultats résumés dans `docs/grille-vigilance.md`.
- **Relecture à froid** par Claude avant la livraison (liste de `pratiques-de-code.md`), de préférence dans une nouvelle session.
- Relecture humaine ciblée par la cellule : authentification, traitement des fichiers déposés, requêtes en base, et tout endroit marqué `À RELIRE` par Claude.
- Dire ce qui n'a pas pu être testé (ex. « non testé sur un poste agent avec l'antivirus de la collectivité ») : `dist/bilan-fabrication.md` en garde la trace.

## 8. Correspondance avec la grille de vigilance

Sujets que couvre généralement une grille de vigilance (modèle à remplir : `grille-vigilance.md`). En cas d'écart, la version de votre cybersécurité fait foi.

| Sujet de la grille | Réponse de conception |
|---|---|
| Stockage de données | Format A sans stockage serveur quand c'est possible ; sinon serveur de la collectivité uniquement, sauvegardé, restauration essayée |
| Connexion à un logiciel métier, l'AD, la messagerie | Seulement si la SPEC le justifie ; compte de service aux droits minimaux, lecture seule si possible |
| Accès depuis Internet | Réseau interne par défaut ; ouverture déclarée et validée selon `ouverture-externe.md` |
| Hors du SI | Jamais pour l'outil en service ; diffusion publique = version dédiée sans données |
| Données personnelles, sensibles | Minimisation ; données fictives en développement |
| Sans avis du DPO | Avis demandé dès la SPEC, avant toute donnée réelle |
| IA externe | Aucune ; IA locale optionnelle avec mode sans IA ; appels sortants limités à `reseau-autorise.txt` |
| Décision par l'IA, sans vérification humaine | L'outil propose, l'agent décide ; pas de tri de personnes sans avis du DPO |
| Secrets en dur | `.env`, `.env.exemple`, contrôle intégré et `gitleaks` |
| Code ni relu ni analysé | `fabriquer.py`, analyses automatiques et relecture ciblée |
| Pas d'authentification | Comptes nominatifs dès qu'il y a des données partagées |
| Mots de passe faibles, comptes partagés | Hachage argon2 ou bcrypt, aucun compte générique (sinon exception notée) |
| Pas de traçabilité | Journal qui / quoi / quand |
| Une seule personne | Référent et suppléant, procédure de mise à jour |
| Pas de documentation, code non remis | Documentation versionnée, dépôt chez la DSI à chaque version |
| *(hors grille)* Composants non maintenus | Règle propre à la skill : `docs/composants.md` avec dates de fin de support, contrôlé par `fabriquer.py` |
