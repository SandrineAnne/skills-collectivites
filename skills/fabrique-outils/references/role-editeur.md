# Notre rôle d'éditeur de solutions internes

Avec Claude, fabriquer un outil ne coûte presque plus rien ; l'entretenir coûte toujours. La collectivité devient donc éditeur de ses propres outils, avec deux devoirs : **libérer la création** (règle d'or de la skill) et **tenir dans la durée** ce qui a été créé. Tout ce qui suit est tenu par Claude, sans charge pour l'agent, et n'est exigé qu'au moment d'une installation durable.

## 1. Rustines : utiles, assumées, avec une date de fin

Beaucoup d'outils comblent un manque : une trame d'agence qui change, un logiciel qui ne produit pas le bon document, un processus pas encore optimisé. C'est légitime, souvent la meilleure réponse en attendant mieux. Une rustine doit simplement dire :
- le problème de fond, et à qui il appartient (agence, éditeur, organisation interne) ;
- s'il a été signalé à qui peut le corriger (« pas encore » est une réponse, que le contrôle rappelle gentiment) ;
- ce dont l'outil dépend (trames, exports, versions) ;
- la condition de retrait, et une date de revue (par exemple avant chaque campagne).

Gabarit : `creer_projet.py --rustine` (fiche `docs/rustine.md`). Le contrôle signale une revue dépassée ; la revue annuelle du parc se demande si le problème de fond est réglé.

**Exemple : le bilan réglementaire d’un service** (à compléter avec le service). Problème de fond : les nouvelles trames des agences, les limites de logiciel métier et le besoin de rapports compréhensibles. Il appartient en partie aux agences (trames), à l'éditeur de logiciel métier (exports) et au service (lisibilité). L'outil dépend de la version de chaque trame et de l'export logiciel métier. Condition de retrait possible : logiciel métier produit lui-même la trame attendue sous une forme lisible. Revue : avant chaque campagne de bilans.

## 2. Contrat d'entrée : ce qu'on reçoit d'ailleurs, décrit et testé

Le point faible d'une rustine, ce sont les fichiers qu'elle reçoit. `docs/entrees.md` décrit chaque format reçu (qui le produit, version, colonnes clés) avec **un exemple inventé** dans `tests/donnees/`. Quand une trame change : une ligne et un exemple de plus, un test qui reconnaît la nouvelle version, et un message clair pour une version inconnue (brique « reconnaître une trame »). Le contrôle exige l'exemple de chaque entrée déclarée pour une installation, et signale un outil qui lit des fichiers sans les décrire.

## 3. Traçabilité des productions

Un rapport qui part vers une agence ou un ministère engage la collectivité. Chaque document produit porte la mention « Produit avec <outil> v<version> le <date> à partir de : <fichiers sources et leur empreinte> » (brique traçabilité). Des mois plus tard, on sait avec quoi il a été fait. Le contrôle signale un outil qui produit des documents sans cette mention.

## 4. L'IA dans les outils

Quand un outil utilise une IA au moment où on s'en sert (modèle local, par exemple), son comportement peut changer avec le modèle. Il faut :
- des **questions-tests** sur des exemples inventés, aux attentes vérifiables, rejouées à chaque changement de modèle et au moins une fois par an (`creer_projet.py --ia`, fichier `tests/ia/questions.md`) ;
- un **mode de secours sans IA**, annoncé à l'écran ;
- des résultats présentés comme des **propositions** que l'agent vérifie (règle 3).

Le contrôle exige les questions-tests pour une installation, et signale celles de plus d'un an.

## 5. Les retours des utilisateurs

Chaque outil propose « Signaler un problème » dans son tutoriel (option `signalement` du module de prise en main), vers le formulaire ou la catégorie « Outils maison » de l’outil de tickets. Un éditeur écoute ses utilisateurs.

## 6. Briques communes

Avec de nombreux agents qui fabriquent, les mêmes besoins reviennent. Plutôt que dix versions du même code, des **briques communes** testées, dans `assets/briques/` : traçabilité et reconnaissance des trames pour commencer. `creer_projet.py --briques` les copie dans `src/briques/` ; on ne les modifie pas dans un projet : une amélioration se propose à la cellule, qui met la brique à jour pour tous. La cellule enrichit la bibliothèque à partir des « briques réutilisables » repérées dans les fiches de partage.

## 7. Arbitrer à l'entrée, revoir le parc chaque année

- **À l'entrée**, la fiche d'une page dit en une ligne pourquoi un outil plutôt que corriger le processus ou demander à l'éditeur. Ce n'est pas un frein : c'est ce qui permet de remonter le problème de fond.
- **Chaque année**, la journée d'entretien décide pour chaque outil : **garder**, **mutualiser** (un autre outil fait la même chose), **retirer** (plus utilisé, ou rustine devenue inutile), ou **remonter au processus** (le problème de fond mérite d'être corrigé à la source). Skill `entretien-outils`, parcours veille.
