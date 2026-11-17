# Parcours 2 — Reprise d'un outil sans dossier

Beaucoup d'outils sont nés avant la fabrique, ou ont été transmis sans explication. Le but n'est pas de les refaire, mais de les rendre **sûrs, compréhensibles et reprenables**, en une session si possible. Principe : **on ne casse rien de ce qui marche** ; on met à l'abri, on documente, puis on améliore par petites étapes.

## 0. Comprendre la situation (questions simples)

- « À quoi sert l'outil, qui l'utilise, à quelle fréquence ? »
- « Qui le connaît encore ? L'auteur est-il joignable ? »
- « Où se trouve-t-il : un fichier qu'on s'envoie, un dossier partagé, un serveur, un programme installé ? »
- « Contient-il des données de personnes ? »

## 1. Mettre à l'abri

- Travailler sur une **copie** ; ne jamais modifier l'original en service.
- Sauvegarder les données de l'outil (pas dans la conversation).
- Un **secret trouvé dans le code** (mot de passe, clé) est considéré comme compromis : le faire renouveler, puis le sortir du code (`.env`).

## 2. Relever l'existant

`python3 scripts/releve_outil.py <copie> --sortie <copie>/docs/releve-existant.md`

Le relevé liste, sans rien modifier : fichiers et format probable, points d'entrée, dépendances (figées ou non), bibliothèques embarquées et leur version, ressources chargées depuis Internet, secrets possibles (valeurs masquées), données de personnes possibles, versions annoncées, éléments de dossier présents ou manquants. Il se trompe parfois : c'est une liste à vérifier, pas une preuve.

## 3. Écrire des tests de caractérisation

Avant toute modification, **figer ce que l'outil fait aujourd'hui** (méthode de Michael Feathers pour le code hérité) : quelques exemples inventés passés dans l'outil, avec le résultat actuel écrit comme résultat attendu. Même si un résultat semble faux, on le fige et on le marque « comportement actuel, à confirmer par le métier ». Ces tests sont le filet de sécurité de toutes les modifications suivantes.

## 4. Reconstruire le dossier

`python3 scripts/remettre_a_niveau.py <copie> --copie --format A|B|C|D [--niveau partage|durable] [--titre "…"]`

Le script ajoute ce qui manque à partir des gabarits de la fabrique et **n'écrase jamais rien** : un fichier présent est conservé ; un README existant reçoit seulement les lignes « Version », « Format » et « Niveau » en tête ; `.gitignore` reçoit la ligne `.env` si elle manque. Quand le code n'est pas dans `src/`, il le déclare dans `build/controles.json` au lieu de le déplacer.

Claude remplit ensuite, avec la personne :
- **README** : à quoi sert l'outil, référent et suppléant (fonctions), démarrage en 5 minutes ;
- **SPEC reconstituée** : règles de gestion déduites du code, chacune marquée « déduite du code, à confirmer par le métier » ; statut « brouillon » jusqu'à la confirmation ;
- **composants** : à partir du relevé, avec les dates de fin de support vérifiées sur le site de chaque éditeur (recherche en ligne, jamais de mémoire) ;
- **décisions** : ce que l'on sait des choix d'origine, et « inconnu » quand on ne sait pas.

## 5. Contrôler en brouillon et prioriser

`python3 build/fabriquer.py --brouillon` donne la liste complète. Traiter dans cet ordre :

1. **Sûreté** : secrets, données de personnes exposées, accès depuis l'extérieur, appels vers l'extérieur non justifiés.
2. **Composants sans support et failles connues.**
3. **Sauvegarde et restauration essayée** (format B), ou version précédente conservée (formats A et C).
4. **Référent et suppléant** désignés.
5. **Tests des règles de gestion** (les tests de caractérisation en sont la base).
6. **Documentation** utilisateur et exploitation.

Ce qui ne peut pas être corrigé tout de suite devient une **exception datée** dans `docs/derogations.md` : rien n'est caché, tout a une date de revue.

## 6. Transmettre

- Envoyer `dist/dossier-transmission.md` à la cellule opérationnelle (statut « à retravailler » ou mieux) et créer ou compléter la carte de l'outil sur le registre des outils avec `dist/fiche-registre.txt`.
- Si personne ne connaît plus l'outil : proposer un **exercice de reprise** au futur suppléant (fiche de partage de la fabrique).
- Si l'outil n'a plus d'usage : proposer sa **fin de vie** (archiver, effacer les données selon la durée convenue avec le DPO, retirer l'adresse et l'inscription dans la supervision).
