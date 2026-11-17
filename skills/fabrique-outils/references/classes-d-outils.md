# Les classes d'outils : l'entretien suit ce que coûte une panne

La classe ne dit pas si un outil est « bien fait » : elle dit ce qui se passe quand il s'arrête. Elle règle l'effort d'entretien, pas la liberté de fabriquer. Claude **propose** une classe dès l'étape 0 (`creer_projet.py --classe N`) ; la **cellule opérationnelle la confirme** à la mise en service et la revoit chaque année. Les délais sont des propositions à valider par la cellule puis la DSI.

| Classe | C'est quand | Si l'outil s'arrête | Remise en marche | Revues | Ce que le dossier doit contenir |
|---|---|---|---|---|---|
| **1. Essentiel** | Utilisé chaque jour par plusieurs agents, ou remplace un logiciel (revue de presse, gestion de projet, agenda partagé…) | Des agents ne peuvent plus travailler | Le jour même | Chaque semestre, et journée annuelle | Niveau durable ; référent et suppléant ; `docs/mode-degrade.md` ; essai de restauration de moins d'un an (outil sur serveur) |
| **2. Important** | Usage régulier dans un service | Gêne, un contournement existe | Dans la semaine | Journée annuelle | Niveau durable recommandé ; référent et suppléant |
| **3. Confort** | Usage ponctuel ou par quelques agents | Peu de gêne | À la prochaine évolution | Revue automatique | Niveau partagé suffisant |

## Ce que le contrôle vérifie

- La classe est une ligne du README (`Classe : 1`, `2` ou `3`) ; tant qu'elle n'est pas renseignée, la livraison durable la réclame (simple alerte en brouillon).
- **Classe 1 au niveau partagé : refusé.** C'est la seule règle de classe qui bloque toujours : un outil dont dépend le travail quotidien ne peut pas rester un simple fichier partagé.
- **Classe 1, pour une installation** : page du mode dégradé présente et remplie ; pour un outil sur serveur, essai de restauration de moins d'un an.
- La fiche du registre reprend la classe et l'état du mode dégradé.

## Règles d'hébergement liées à la classe

- Un outil de classe 1 ne tourne **jamais sur un serveur de test** : production, données sous `/data` (la supervision ne sauvegarde que ce qui s'y trouve), sonde de supervision sur son adresse de santé.
- Un outil qui **remplace un logiciel** est de classe 1 d'office ; l'ancien logiciel reste consultable pendant la bascule, et la cellule et la DSI décident ensemble du jour où l'on ne revient plus en arrière.
- Les mêmes classes s'appliquent aux logiciels libres installés par nos soins (gestion de projet, wiki, réservations…) : la fabrique ne les concerne pas, la skill d'entretien oui.
