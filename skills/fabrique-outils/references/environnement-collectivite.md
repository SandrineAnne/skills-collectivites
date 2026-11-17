# Environnement de votre collectivité

**À adapter avant tout usage.** Tout ce qui dépend de l'organisation est ici et nulle part ailleurs : rôles, contraintes, serveurs, postes, outils d'exploitation. Les autres fichiers de la skill ne contiennent que des principes. Les exemples entre parenthèses sont ceux d'une collectivité qui utilise déjà la méthode, donnés à titre indicatif.

## Rôles et validations

| Qui | Rôle dans la méthode |
|---|---|
| Cellule opérationnelle (ou équivalent) | Recueille le besoin ; valide la fiche d'une page, le prototype et la recette ; valide la mise en service des outils verts ; tient le rôle de « référent IA » de la grille ; tient le registre des outils |
| Émetteur du besoin | Questionné au départ ; fait la recette métier |
| Cybersécurité | Tient la grille de vigilance ; avis requis pour les niveaux orange et rouge |
| DPO | Avis avant tout traitement de données personnelles ; avis préalable pour tout outil qui classe ou trie des personnes |
| DSI | Reçoit le code à chaque version ; héberge et expose les applications |
| Chef de projet chargé de l'entretien | Entretient l'outil (exemple : le chef de projet du progiciel du même domaine) |

## Contraintes

- **IA externes :** [À ADAPTER] (exemple : aucune application n'appelle une API d'IA externe ; IA locale en option seulement, avec un mode sans IA).
- **Données réelles :** aucune donnée réelle de personne n'est confiée à l'IA qui fabrique ; transcriptions anonymisées, jeux de données fictifs.
- **Charte graphique :** [À ADAPTER] (couleurs, police, logo ; une skill dédiée si vous en avez une).
- **Langue :** interface, messages, documentation et commentaires dans la langue des agents.

## Hébergement des applications web

- Système, moteur de conteneurs : [À ADAPTER] (exemple : Ubuntu 24.04, Podman ou Docker, compose).
- Dossier par application : [À ADAPTER] (exemple : `/data/apps/<nom>`, seul emplacement sauvegardé).
- Adresse : [À ADAPTER] (exemple : `<nom>.exemple.fr`).
- Frontal : [À ADAPTER] (exemple : nginx de l'hôte, un vhost par application, réseau interne seulement par défaut).
- Réseau interne autorisé dans les vhosts : [À ADAPTER] (le gabarit met `10.0.0.0/8` comme exemple).
- Déploiement : [À ADAPTER] (les playbooks fournis tournent avec Ansible, par exemple depuis Semaphore).

## Postes de travail

- Programmes installés : [À ADAPTER] (exemple : PyInstaller dans un MSI, diffusé par l'outil de télédistribution).
- Signature des exécutables et antivirus : [À ADAPTER].

## Outils d'exploitation

- Tickets : [À ADAPTER] (une catégorie « Outils maison » est recommandée).
- Supervision des applications et des serveurs, sauvegarde et restauration : [À ADAPTER].
- Dépôt de code : [À ADAPTER].
- Wiki ou documentation partagée : [À ADAPTER].
- Registre des outils : [À ADAPTER] (exemple : un tableau partagé sur l'intranet, une carte par outil).
