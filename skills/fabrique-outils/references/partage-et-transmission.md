# Partager l'outil et transmettre le savoir-faire

Credo : **un outil fabriqué dans une licence ne doit pas rester dans cette licence si d'autres peuvent en profiter.** La collectivité a tout à gagner à ce que les bonnes idées circulent. Cette fiche dit comment le repérer, comment le dire avec bienveillance (et un peu d'humour), et comment transmettre le savoir-faire pour que l'outil survive à son auteur.

## Repérer le potentiel de réutilisation

Claude y pense à trois moments : étape 0 (le besoin), jalon 2 (le prototype) et à la livraison. Il y a potentiel quand **au moins deux** signaux sont réunis :

- le besoin n'est pas propre à une direction (comparer, convertir, rapprocher, calculer, cartographier, pseudonymiser, suivre des échéances…) ;
- l'agent dit que des collègues font pareil, « chacun dans son Excel », ou que ça lui a pris des heures ;
- le besoin touche un métier transversal (finances, RH, marchés publics, courriers, archives, bâtiments, cartes, communication) ;
- l'outil est déjà paramétrable (listes, seuils, libellés en configuration) : une autre direction peut le reprendre en changeant un fichier ;
- l'outil ressemble à un outil du registre (`registre-des-outils.md`) : soit on réutilise l'existant, soit on le complète ;
- l'outil contient une **brique réutilisable** (import Excel, rapprochement chiffré, export propre, fond de carte, tutoriel) que d'autres pourraient reprendre.

Ce que l'on partage, c'est l'**outil et son mode d'emploi**, jamais les données (aucune donnée de personne ou confidentielle ne circule).

## Poser les bases dès le début : appeler la cellule tôt

Le meilleur moment pour parler à la cellule opérationnelle n'est pas la livraison, c'est le début. Une fois l'outil fabriqué, un changement de fond coûte cher ; avant, la cellule peut dire « cela existe déjà », « utilisez plutôt tel standard », ou « oui, nous pourrions l'installer ». Dès la SPEC (jalon 1), Claude fait trois gestes, sans ralentir l'agent :

1. **Il pose la question en mots simples :** « Cet outil restera-t-il pour vous ou vos collègues, ou la cellule pourrait-elle un jour l'installer pour d'autres ? » La réponse est notée dans `docs/partage.md` (« Demande d'installation » : oui, non, plus tard ; « je ne sais pas » vaut « plus tard »).
2. **Il crée le dossier avec les bons gabarits.** Le niveau (partagé ou durable) se choisit sans en parler à l'agent : même structure pour tous, donc transmissible dès le premier jour, et on peut monter de niveau sans rien perdre.
3. **Il propose un signalement de trois lignes à la cellule** (nom, besoin, qui l'utilise), sous la forme d'une carte dans la colonne d'entrée du registre des outils de la collectivité : « Je peux prévenir la cellule en trois lignes, pour qu'elle vous dise tout de suite si cela existe déjà ou si elle peut vous aider. » Facultatif, jamais bloquant.

Ensuite, à chaque contrôle, `fabriquer.py` écrit `dist/dossier-transmission.md` : un résumé d'une page, avec un statut que l'agent peut envoyer tel quel **à tout moment**, même inachevé. La cellule décide alors si elle aide à terminer.

| Statut | Ce que cela veut dire pour la cellule |
|---|---|
| Brouillon, pas encore transmissible | L'agent travaille ; rien à faire, mais elle peut donner un avis tôt |
| À retravailler avant installation | Des points bloquants sont listés ; elle peut proposer son aide |
| Installable avec réserves | Prêt, avec des points à regarder ensemble (essai de restauration, exceptions) |
| Prêt à installer | Rien ne manque : elle peut planifier l'installation |
| Utilisable par des collègues (niveau partagé) | Un simple fichier partagé ; elle est informée, il n'y a rien à installer |

## Le message : amical, drôle, jamais culpabilisant

Règles : **un seul message par session**, seulement quand le potentiel est réel, jamais de reproche, toujours une invitation avec une action simple et proposée. Varier la formule. Terminer par un choix : *(a) je rédige un message à la cellule opérationnelle · (b) je prépare la fiche pour l'intranet · (c) pas maintenant*.

Formules possibles :

1. « 🎁 Alerte trésor : votre outil ressemble beaucoup à ce dont d'autres services ont besoin. Un outil qui dort dans une seule licence, c'est un vélo électrique dans un garage : très bien… mais les voisins marchent. Si on le présentait à la cellule opérationnelle ou dans l'intranet ? Cinq lignes suffisent, je les rédige. »
2. « 🕵️ Chut… j'ai repéré un outil trop bon pour rester seul. L'égoïsme d'usage guette : ça commence par « c'est juste pour moi » et ça finit par trois directions qui refont chacune la même chose dans leur coin. On l'arrête ensemble ? »
3. « 🍰 Un bon outil, c'est comme un bon gâteau : plus on le partage, plus il y a de monde pour dire qu'il est bon (et pour suggérer qu'on y mette moins de sucre). Voulez-vous le faire connaître à la cellule opérationnelle ? »
4. « ⚠️ Mise en garde amicale : garder cet outil pour vous peut provoquer, chez vos collègues, des heures perdues et de grands soupirs devant Excel. Remède : le signaler à la cellule ou dans l'intranet. Efficacité garantie, effets secondaires : des remerciements. »
5. « 🎉 Bravo : vous avez peut-être fabriqué ce que trois services cherchent encore ! On ne va pas en faire un secret d'État. Je vous prépare la fiche de présentation ? »
6. Pour la transmission : « 🔧 Un outil que personne d'autre ne sait réparer a un point de vigilance… et un suppléant à qui vous devez au moins un café. On organise une petite passation ? »

Si l'agent répond « pas maintenant » : respecter, noter « non souhaité pour l'instant, raison » dans `docs/partage.md`, et ne reposer la question **qu'une seule fois**, à la livraison.

## Faire connaître l'outil

La **fiche de présentation** tient en cinq lignes ; Claude la rédige à partir de `docs/partage.md` et de la SPEC :
- le nom et à quoi sert l'outil, avec les mots du métier ;
- qui peut l'utiliser (profils, services concernés) ;
- ce qu'il faut pour le reprendre : ce qui est propre à la direction d'origine et se règle en configuration ;
- le référent et le suppléant (par fonction) ;
- où le trouver (dépôt, adresse) et quel niveau de contrôle de sécurité (vert, orange).

Elle est adressée à la **cellule opérationnelle**, qui décide du référencement (inventaire des outils, diffusion à d'autres directions) et de la publication dans l'**intranet** (modalités à préciser avec la cellule : voir `decisions-a-prendre.md`). Claude propose de rédiger le message d'envoi.

Quand un autre service veut reprendre l'outil : la cellule examine si la reprise est directe (changer la configuration), si une adaptation est nécessaire (nouvelle SPEC, nouvelle version), ou s'il faut passer en niveau supérieur du curseur (nouvelles données, nouveaux utilisateurs).

## Transmettre le savoir-faire

Un outil durable, c'est aussi des personnes capables de le comprendre. À la livraison, Claude propose, sans l'imposer :

1. **Un exercice de reprise (30 minutes)** : le suppléant, ou un collègue, rejoue l'installation ou la mise à jour sur le serveur de test avec la seule documentation. Ce qui bloque est noté et corrigé dans la documentation.
2. **Une courte présentation** (20 minutes) à la cellule ou à des pairs : à quoi sert l'outil, comment il a été fabriqué avec Claude, ce qui a surpris.
3. **« Ce que j'ai appris »** : trois conseils de l'agent pour la prochaine personne (une astuce de prompt, un piège évité, un réflexe de vérification), remis à la cellule, qui enrichit la skill, les exemples et le dialogue.
4. **La page « reconstruction »** de la documentation (`livraison.md`) : de quoi refaire l'outil sans Claude.

Ces actions se notent dans `docs/partage.md` (date, fonction). `build/fabriquer.py` signale à la livraison un outil réutilisable qui n'a pas été signalé à la cellule, sans bloquer.
