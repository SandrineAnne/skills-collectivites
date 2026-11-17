# Pratiques de code : ce que font les meilleures équipes, et comment la skill l'applique

Tout ce qui suit est appliqué par Claude sans rien demander à l'agent (voir `dialogue-agent.md`). Chaque pratique dit d'où elle vient, ce que Claude fait, et ce qui la vérifie. Quand une pratique est vérifiée par une machine, elle ne dépend plus de la bonne volonté de personne : c'est le but.

## Les pratiques

| # | Pratique | D'où elle vient | Ce que fait Claude | Ce qui le vérifie |
|---|---|---|---|---|
| 1 | **Écrire ce qu'on attend avant de coder** | Développement piloté par les tests (Kent Beck) | Chaque règle de gestion (RG) a un exemple chiffré dans la SPEC, puis un test | `fabriquer.py` : chaque RG a un test, **et les tests sont exécutés** |
| 2 | **Un cœur pur, des bords minces** | « Functional core, imperative shell » (Gary Bernhardt), architecture hexagonale | Les règles métier sont dans `src/coeur/`, sans fichier, sans réseau, sans écran ; l'interface et les lectures de fichiers les appellent | Les tests du cœur tournent sans navigateur ni serveur |
| 3 | **Le plus simple qui marche** | Règles de conception simple (Beck), YAGNI | Format le plus simple, pas de fonction « au cas où », pas de dépendance évitable ; le reste va dans « Hors périmètre » | Relecture à froid ; alerte sur les fonctions de plus de 80 lignes |
| 4 | **Les mots du métier dans le code** | Conception pilotée par le domaine (Eric Evans) | Fonctions, variables et messages reprennent les mots de la SPEC, en français | Relecture à froid |
| 5 | **Un seul bouton pour tout contrôler** | Intégration continue, « construire en une étape » | `python3 build/fabriquer.py` fait tous les contrôles et fabrique le paquet | Le script lui-même ; son autotest (`autotest_fabrique.py`) |
| 6 | **Échouer tôt, clairement, jamais en silence** | The Pragmatic Programmer | Entrées validées à la frontière ; message utile à l'agent ; détail technique dans le journal ; aucune erreur avalée | `fabriquer.py` : `except:` sans type refusé, `pass` silencieux signalé |
| 7 | **Un défaut corrigé = un test ajouté** | Tests de non-régression | Avant de corriger, écrire le test qui échoue ; il reste dans `tests/` | Les tests exécutés à chaque fabrication |
| 8 | **Des tests rapides et déterministes** | Pyramide des tests (Mike Cohn) | Beaucoup de tests du cœur, peu de tests d'interface ; pas de réseau, pas de date du jour, pas d'aléa dans un test | Durée limitée par commande de test (`--delai-tests`) |
| 9 | **La sécurité se conçoit, elle ne s'ajoute pas** | OWASP (Top 10, ASVS, aide-mémoire), guides de l'ANSSI | Moindre privilège, entrées non fiables, requêtes paramétrées, pas de HTML construit avec des données reçues | `fabriquer.py` : motifs dangereux refusés ; `bandit`, `ruff` ; grille de vigilance |
| 10 | **Maîtriser ce qu'on embarque** | Chaîne d'approvisionnement logicielle (SLSA, OpenSSF) | Versions figées, empreintes, liste des composants avec fin de support, délai de carence de 14 jours | `fabriquer.py` : dépendances et images figées ; `pip-audit`, `npm audit`, `trivy` ; empreinte SHA-256 du paquet |
| 11 | **Même chose en test et en production** | Application à douze facteurs (12factor.net) | Configuration dans `.env`, application sans état, journaux sur la sortie standard, mêmes fichiers et mêmes contrôles sur les deux serveurs | `playbook_check.yaml` rejoué à l'identique ; `essai_playbooks.py` |
| 12 | **Déployer sans peur : petit, vérifié, réversible** | Infrastructure comme du code | Playbooks versionnés, image précédente gardée (`avant-maj`), attente de l'adresse de santé, retour arrière écrit | `essai_playbooks.py` ; contrôle de version en service |
| 13 | **Savoir dans quel état est l'outil** | Observabilité | Une adresse `/sante` qui répond 200 et donne la version ; journal « qui, quoi, quand » | `playbook_check.yaml` |
| 14 | **Des versions qui veulent dire quelque chose** | Versionnage sémantique (semver.org), Keep a Changelog | x.y.z dans le seul fichier `VERSION` ; une entrée de CHANGELOG par version, en langage métier | `fabriquer.py` : version identique partout |
| 15 | **Noter pourquoi, pas seulement quoi** | Journaux de décisions d'architecture (Michael Nygard) | `docs/decisions.md` : chaque choix technique, sa raison, la solution écartée ; commentaires qui expliquent le pourquoi | Alerte si aucune décision n'est notée |
| 16 | **Relire avant de livrer** | Revue de code (pratiques d'ingénierie de Google) | Relecture à froid par Claude, puis relecture humaine ciblée par la cellule | Liste ci-dessous ; points marqués `À RELIRE` |
| 17 | **Laisser le code plus propre qu'on l'a trouvé** | Réusinage sous tests (Martin Fowler) | À chaque évolution : simplifier ce qu'on touche, jamais sans tests qui passent avant et après | Les tests exécutés ; conseils de `ruff` |
| 18 | **Valider à la frontière, avec un contrat** | Conception par contrat, validation des entrées | `docs/entrees.md` + un exemple par format reçu ; message clair pour un format inconnu (brique) | `fabriquer.py` : exemple exigé pour chaque entrée déclarée |
| 19 | **Pouvoir dire avec quoi un résultat a été produit** | Provenance et reproductibilité | Mention « Produit avec … » sur chaque document (brique traçabilité) | Alerte si un outil produit des documents sans la mention |
| 20 | **Évaluer ce qui n'est pas déterministe** | Évaluation des systèmes d'IA | Questions-tests aux attentes vérifiables, rejouées à chaque changement de modèle ; mode de secours sans IA | Questions-tests exigées pour une installation ; alerte au-delà d'un an |

## La relecture à froid (avant chaque livraison)

Claude relit le code comme s'il ne l'avait pas écrit — de préférence dans une nouvelle session ou avec un sous-agent qui ne reçoit que la SPEC et le code, sans la conversation — et répond par écrit, dans `docs/grille-vigilance.md`, à ces questions :

1. Un collègue comprend-il chaque fonction en la lisant une seule fois ? (nom, longueur, un seul rôle)
2. Chaque donnée qui vient de l'extérieur (fichier, saisie, adresse) est-elle contrôlée à l'entrée ?
3. Que se passe-t-il avec un fichier vide, énorme, mal formé, ou une cellule qui commence par `=` ?
4. Une erreur peut-elle passer inaperçue ? Chaque message d'erreur aide-t-il l'agent à s'en sortir ?
5. Reste-t-il du code mort, du code dupliqué, une dépendance dont on peut se passer ?
6. Toutes les règles métier sont-elles dans `src/coeur/`, testées sans interface ?
7. Une donnée de personne peut-elle fuir : journal, message d'erreur, stockage du navigateur, export ?
8. Le retour arrière est-il écrit, et a-t-il été essayé ?
9. Qu'est-ce qui n'a **pas** été testé ? Le dire dans le message de fin.

Les endroits qui méritent un œil humain (authentification, fichiers déposés, requêtes en base, calculs financiers) sont marqués `À RELIRE` dans le code et listés à la cellule.

## Liberté d'abord : un socle de sûreté pour tous, la complétude selon le niveau

Le contrôle ne doit jamais empêcher un agent de fabriquer ni d'utiliser son outil. Il distingue deux choses :

| | **Socle de sûreté** (toujours bloquant) | **Complétude** (selon le niveau) |
|---|---|---|
| Ce que c'est | Secrets en dur, appel externe non déclaré, code dangereux, faute de syntaxe, test qui échoue, faille connue | SPEC validée, règles testées, tests présents, composants listés, documentation, essai de restauration |
| Niveau partagé (un HTML pour des collègues) | Exigé | Recommandé : alerte, jamais bloquant |
| Brouillon (`--brouillon`) | Exigé | Alerte : on travaille librement |
| Niveau durable, livraison | Exigé | **Exigé** : c'est la condition pour que la cellule installe l'outil |

Dans tous les cas, `dist/dossier-transmission.md` est écrit : un résumé d'une page et un statut (brouillon, à retravailler, installable avec réserves, prêt à installer) que l'agent peut envoyer à la cellule quand il veut.

## Ce que `fabriquer.py` refuse, signale, ou laisse au jugement

| Refusé (pas de paquet) | Signalé (alerte) | Laissé au jugement |
|---|---|---|
| Test en échec, ou aucun test exécuté | Fonction de plus de 80 lignes | Clarté des noms |
| Erreur de syntaxe Python ou JavaScript | Erreur avalée (`pass`) sans commentaire | Pertinence des tests |
| `eval`, `exec`, `shell=True`, `os.system`, `pickle`, SQL construit avec du texte, `verify=False`, `document.write` | HTML inséré par le code (`innerHTML`), stockage du navigateur | Justesse des règles métier (recette) |
| `except:` sans type | Empreintes de dépendances absentes | Ergonomie |
| Dépendance ou image non figée ; secret ; appel réseau non déclaré | Conteneur en root, durcissement absent sans exception notée | |
| Faille connue (`pip-audit`, `npm audit`, `trivy`), défaut `bandit` de gravité moyenne ou haute, erreur `ruff` | Essai de restauration absent ou ancien ; composant en fin de support dans 6 mois | |

Un motif refusé mais justifié se marque sur la ligne : `nosec : raison` (code) ou `nosecret : raison` (exemple fictif de secret). La raison est obligatoire : sans elle, le marqueur ne compte pas. Chaque exemption est recopiée dans `dist/bilan-fabrication.md` et comptée dans la fiche du registre : la cellule les relit une à une. Ne jamais poser une exemption pour faire passer le contrôle ; corriger d'abord.

## Options utiles de `fabriquer.py`

- `--brouillon` : contrôle d'étape pour travailler librement ; les tests sont exécutés et le socle de sûreté reste exigé, mais la complétude (champs à compléter, SPEC non validée, tests ou composants absents) ne bloque pas.
- Niveau partagé : écrire `Niveau : partagé` dans le README (ou créer le projet avec `--niveau partage`) ; réservé au format A.
- `--exiger-analyses` : un outil d'analyse absent (`ruff`, `bandit`, `pip-audit`, `gitleaks`, `node`) devient une erreur. **À utiliser pour tout outil orange**, et sur la machine qui fabrique la version livrée.
- `--analyser-images` : analyse les images du compose avec `trivy` (long, demande le réseau).
- `build/controles.json` : `{"tests": [["commande", "argument"]]}` pour déclarer ses propres commandes de test (Playwright, par exemple), et `{"code": ["index.html", "app/"]}` pour un outil repris dont le code n'est pas dans `src/`.
- Sans option, un outil absent est écrit sous « Non testé » dans le bilan : rien n'est caché.

## Installer les outils d'analyse (une fois, sur le poste ou dans Cowork)

`pip install pytest ruff bandit pip-audit` ; `gitleaks` et `trivy` s'installent à part (binaires). Sans eux, `fabriquer.py` fonctionne quand même : il exécute les tests avec son lanceur intégré, contrôle la syntaxe, les motifs dangereux, les secrets et les dépendances, et dit ce qu'il n'a pas pu faire.
