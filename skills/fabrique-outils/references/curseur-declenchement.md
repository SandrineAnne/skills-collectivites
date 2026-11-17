# Le curseur : quand la skill se déclenche, et à quelle hauteur

La skill complète est faite pour des outils qui vont durer. Pour un fichier jetable, elle serait une lourdeur. Le critère n'est **pas le format** (un simple HTML peut être un outil important) mais **qui l'utilise, combien de temps, avec quelles données**.

## Une seule question pour placer le curseur

> « Cet outil servira-t-il à d'autres personnes que vous, ou plusieurs fois dans la durée ? »

Si la réponse n'est pas évidente, Claude la pose (en mots simples) avant de choisir le niveau.

## Les trois positions (plus une porte d'avis)

| Niveau | Quand | Ce que fait Claude |
|---|---|---|
| **0. Jetable** | Un fichier pour soi ou pour une réunion, durée de vie courte (un comité, un rapport, un diaporama), aucune donnée de personne, aucune reprise par d'autres. Exemples : calculette, graphique de diaporama, mini-tableau de bord ponctuel d'un fichier Excel | La skill **ne se déclenche pas**. Les règles minimales des instructions générales suffisent (voir plus bas). Claude peut glisser une phrase : « Si d'autres en ont l'usage, dites-le-moi : on passera en version durable. » |
| **1. Partagé** (voie courte) | Un HTML autonome (format A) utilisé par quelques collègues, montré plusieurs fois aux élus ou à une direction, ou qui présente des chiffres de référence ; sans donnée de personne. Exemples : tableau de bord ou carte repris chaque année, simulateur partagé, automatisation ponctuelle sur poste qui sert pendant des années (bilan réglementaire d’un service) | La skill se déclenche en **voie courte** (niveau « vert » de la grille) : `creer_projet.py --niveau partage` crée un dossier léger ; SPEC de cinq lignes, en-tête visible (nom, version, date, référent), bibliothèques embarquées, chiffres rapprochés de la source, tutoriel court, fiche de partage. Pas de jalons formels. `fabriquer.py` n'exige alors que le socle de sûreté (secrets, appels externes, code dangereux, tests en échec s'il y en a) : documentation, tests et composants restent des recommandations |
| **2. Durable** (voie complète) | Au moins un de ces critères : serveur (B), poste (C) ou document Grist partagé (D) ; données de personnes (agents, usagers) ou sensibles ; connexion à un logiciel, à l'annuaire ou à la messagerie ; remplace un outil existant ; outil essentiel (classe 1) ; installation demandée pour d'autres par la cellule ; présenté comme référence aux élus ; grille orange | Méthode complète : SPEC, jalons, socle, `fabriquer.py`, paquet d'intégration |
| **3. Avis d'abord** | Service au public, ouverture à des externes, point bloquant de la grille, grille rouge | La skill s'arrête dès la SPEC : avis de la DSI, de la cybersécurité, du DPO et de la direction concernée (`ouverture-externe.md`) |

**La durée seule ne fait pas un outil durable.** Un fichier HTML local, sans serveur, sans appel extérieur et sans donnée de personne, utilisé de temps en temps sur un poste, reste en voie courte même s'il sert pendant des années : ce qui fait monter le curseur, c'est le risque (serveur, données de personnes, logiciel connecté, outil essentiel), pas l'âge de l'outil.

**Le curseur monte, il ne descend pas sans l'accord de la cellule.** Dès qu'un critère d'un niveau supérieur apparaît en cours de route (« d'autres directions le veulent », « on va y mettre de vraies données », « on l'ouvre aux communes »), Claude le dit simplement et propose de monter d'un cran, en reprenant ce qui existe déjà.

## Cas d'école (à ajuster par la cellule)

| Demande | Niveau |
|---|---|
| « Remplir la trame d'un rapport à partir des fichiers reçus, sur mon poste, à chaque campagne » (bilan réglementaire) | 1. Partagé : voie courte, classe 3 ; un exemple inventé de chaque trame reçue est recommandé |
| « Un graphique pour mon diaporama à partir de ce fichier » | 0 |
| « Une calculette pour estimer un montant, pour moi » | 0 |
| « Une carte interactive pour le comité de jeudi » | 0 |
| « La même calculette, mais mes collègues du service veulent l'utiliser » | 1 |
| « Un tableau de bord de suivi que les directeurs ouvriront chaque semaine » | 1 |
| « Une carte mise à jour chaque année et montrée aux élus » | 1 |
| « Un outil qui compare des devis, avec des montants réels, pour tout le service » | 2 |
| « Un outil pour pseudonymiser des dossiers (RH, social) » | 2 (données de personnes, même en local) |
| « Une application web de suivi avec des comptes agents » | 2 |
| « Remplacer ce fichier Excel partagé par une vraie application » | 2 |
| « Un formulaire pour les communes » | 2, puis 3 (ouverture externe) |
| « Une appli pour les parents d'élèves du territoire » | 3 |

## Règles minimales pour le niveau 0

Ces cinq règles ne dépendent pas de la skill : elles figurent dans les instructions générales du compte, toujours chargées. Texte à ajouter par l'administrateur, par exemple comme point 6 des instructions générales du compte Claude de votre organisation :

```
6. Outils HTML et tableaux de bord
- Avant de construire un outil, tableau de bord, formulaire ou page interactive, se demander : « servira-t-il à d'autres personnes que son auteur, ou plusieurs fois dans la durée, ou avec des données de personnes ? » Si oui, ou en cas de doute : charger la skill fabrique-outils.
- Sinon (fichier jetable pour soi ou pour une réunion), appliquer ces règles minimales : (a) aucune donnée de personne réelle ; (b) aucune ressource chargée depuis Internet, sauf nécessité déclarée ; jamais d'appel à l'API Anthropic ; (c) aucun mot de passe ni clé écrit dans le fichier ; (d) un en-tête discret « Outil de travail, version, date, auteur (fonction) » ; (e) si les chiffres viennent d'un fichier, les rapprocher de la source avant de les présenter.
- Si l'outil devient utile à d'autres, le dire à l'auteur avec bienveillance et passer en version durable.
```

## Pourquoi pas « tout ou rien »

- Un seuil trop bas alourdit la fabrication de choses simples : les agents contournent la skill.
- Un seuil trop haut laisse passer des outils qui se diffusent sans garde-fous (un « petit » HTML repris par dix personnes devient un outil de production).
- La question unique et le principe « le curseur monte » règlent les deux risques.

## À valider par la cellule

Le nombre de personnes à partir duquel un outil est « partagé » (ici : dès qu'une personne autre que l'auteur l'utilise régulièrement) et la liste des cas d'école. La skill s'essaie ensuite sur une douzaine de demandes réelles, pour vérifier qu'elle se déclenche au bon niveau (voir `fiche-observation-test.md`).
