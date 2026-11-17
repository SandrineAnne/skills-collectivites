# Qui fait quoi, et ce qui n'est pas encore décidé

## Claude prépare, un humain habilité exécute

Claude ne touche jamais lui-même à un serveur de production ni à la diffusion d'un outil aux utilisateurs. Il prépare les correctifs, les commandes, les playbooks et les messages ; la personne qui en a le droit les exécute.

## Les rôles (par fonction)

| Rôle | Ce qu'il fait dans l'entretien | État |
|---|---|---|
| Référent métier et suppléant | Signalent, recettent les corrections, informent les utilisateurs, tiennent le contenu métier à jour | En place |
| Chef de projet chargé de l'entretien | Le chef de projet du progiciel du même domaine (rattachement par thème) : traite les tickets avec cette skill, publie les versions, tient la fiche du registre | **Décidé** par la cellule (11/2026) |
| Responsable du parc (cellule opérationnelle) | Porte d'entrée, registre registre, tri, revues trimestrielle et semestrielle, journée annuelle | Proposé |
| Unité qui reçoit les tickets | Vérifie le ticket, oriente vers le chef de projet, donne le mode dégradé pour un outil de classe 1 | À confirmer |
| Administrateur infrastructures, ingénieur système et base de données | Retour arrière, restauration, déploiement par les playbooks, sauvegardes, bases | En place |
| Administrateur identités, unité réseaux | Accès et comptes ; adresses, certificats, filtrage | En place |
| Ingénieurs sécurité (RSSI) et DPO | Avis, campagnes de failles ; tout incident touchant des données de personnes | En place |

## Qui agit en production (proposition à valider)

| Geste | Qui |
|---|---|
| Rediffuser la version précédente d'un fichier HTML (format A) | Référent de l'outil, depuis le lieu de téléchargement |
| Retour arrière ou restauration d'une application web (format B) | Chef de projet, avec l'administrateur infrastructures, depuis la supervision |
| Déploiement d'une correction ou d'une évolution (format B) | Chef de projet, par les playbooks (Semaphore) |
| Rediffusion d'un programme sur les postes (format C) | Exploitation, par l'outil de diffusion des logiciels, à la demande du chef de projet |
| Restauration d'un document Grist (format D) | Référent du document |
| Prévenir le DPO ou la cybersécurité | Référent, chef de projet ou cellule, sans attendre ; Claude aide à écrire le message |
| Décider de la fin de vie d'un outil | Service demandeur, avec la cellule |

## Classes et délais (proposition, détail dans `classes-d-outils.md` de la fabrique)

| Classe | Remise en marche | Revue |
|---|---|---|
| 1. Essentiel (chaque jour, ou remplace un logiciel) | Le jour même ; mode dégradé donné aux agents tout de suite | Chaque semestre, et journée annuelle |
| 2. Important | Dans la semaine | Journée annuelle |
| 3. Confort | À la prochaine évolution | Revue automatique |

La gravité d'un incident (bloquant, gênant, mineur) se lit avec la classe : un incident bloquant sur un outil de classe 1 passe avant tout le reste.

## Décisions en attente

| Sujet | En attendant | Décideur | Échéance |
|---|---|---|---|
| Classes et délais | Appliquer le tableau ci-dessus | Cellule, puis DSI | À fixer |
| Responsable du parc et suppléant | La cellule dans son ensemble | Cellule | À fixer |
| Catégorie « Outils maison » dans l’outil de tickets, unité qui reçoit les tickets | Signalement au référent, qui prévient la cellule | DSI | À fixer |
| Qui a le droit d'agir en production, selon le format | Appliquer le tableau ci-dessus ; en cas de doute, la cellule décide | Responsables de service | À fixer |
| Où vivent les dossiers des outils (pour la revue de `veille_outils.py`) | Le dépôt de code de la DSI dès qu'il est arrêté ; à défaut, le partage désigné par la cellule | DSI | À fixer |
| Date de la première journée annuelle d'entretien | Hors préparation budgétaire et congés d'été | Cellule | À fixer |
| Conservation des journaux et des sauvegardes d'outil | Selon l'avis du DPO, outil par outil | DPO | À fixer |
