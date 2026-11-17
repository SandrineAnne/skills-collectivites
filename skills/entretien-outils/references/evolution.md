# Parcours 3 — Évolution

Une évolution part toujours d'une demande en mots simples et passe par la SPEC avant le code. Elle laisse l'outil plus propre qu'elle ne l'a trouvé.

## 1. Comprendre la demande

- « Qu'est-ce qui changera pour les utilisateurs ? » (une phrase, avec les mots du métier)
- « Qui le demande, et pourquoi maintenant ? » (une règle qui change, un nouveau besoin, d'autres services intéressés)
- « Comment saura-t-on que c'est réussi ? »

## 2. Mesurer l'impact

| Question | Si oui |
|---|---|
| Une règle de gestion est ajoutée ou modifiée ? | Nouvelle RG ou RG modifiée dans la SPEC, avec un exemple chiffré, puis son test |
| De nouvelles données, en particulier des données de personnes ? | Réévaluer la grille de vigilance (données personnelles et sensibles, avis du DPO) ; avis du DPO si nécessaire |
| De nouveaux utilisateurs, d'autres services, l'extérieur ? | Le curseur de la fabrique monte peut-être (partagé → durable, ou avis d'abord) |
| Une connexion à un logiciel, à l'annuaire, à la messagerie ? | Grille (connexion à un logiciel) et choix de l'accès avec la DSI |
| Une nouvelle bibliothèque ou image ? | `docs/composants.md`, version figée, date de fin de support vérifiée ; délai de carence de 14 jours pour une version toute neuve |
| Un autre format (fichier → serveur) ? | Ce n'est plus une évolution : nouvelle SPEC avec la fabrique, en reprenant le cœur métier |

## Cas fréquent : une source change de format

Une agence publie une nouvelle trame, un logiciel modifie son export. C'est l'évolution la plus courante d'une rustine :
1. ajouter un exemple inventé de la nouvelle version dans `tests/donnees/` et une ligne dans `docs/entrees.md` ;
2. ajouter la version à la brique « reconnaître une trame » de l'outil et un test qui la reconnaît ;
3. garder la lecture des anciennes versions tant qu'elles circulent ;
4. version évolutive (`nouvelle_version.py … evolution "Nouvelle trame 2027 reconnue"`) ;
5. relire la fiche rustine : signaler le changement au propriétaire de la trame, ajuster la date de revue.

## 3. Choisir la nature de la version

| Nature | Numéro | Exemples | Validation |
|---|---|---|---|
| Correction | x.y.**z** | Un défaut corrigé, un libellé | Aucune : le test suffit |
| Évolution compatible | x.**y**.0 | Une colonne, un export, un filtre ; les anciennes sauvegardes restent lisibles | Confirmation du référent |
| Changement d'usage ou de données | **x**.0.0 | Nouvelle donnée de personne, nouveaux utilisateurs, format des sauvegardes changé, règle de calcul modifiée | SPEC revalidée par la cellule (jalon 1 de la fabrique), grille réévaluée |

## 4. Faire

1. **SPEC d'abord** : la règle ajoutée ou modifiée, avec son exemple ; une ligne dans `docs/perimetre.md` si elle n'était pas prévue.
2. **Test d'abord** : le test de la nouvelle règle échoue avant le code.
3. **Code** : la plus petite modification qui fait passer le test ; puis simplifier ce qu'on a touché, sous tests (« laisser plus propre »).
4. **Compatibilité** : un outil qui garde des données lit encore les anciennes (fichier de sauvegarde d'une version précédente converti, migration de base numérotée et rejouable) ; pour un outil sur serveur, « cloner, tester, puis produire » (fiche `scripts-exploitation.md` de la fabrique).
5. `python3 scripts/nouvelle_version.py <dossier> evolution "Ce qui change pour les utilisateurs"` (ou `majeure`).
6. `python3 build/fabriquer.py` ; puis serveur de test, puis production, par une personne habilitée.
7. **Faire connaître** : CHANGELOG en langage métier, encadré « Nouveautés » du tutoriel de prise en main, information de la cellule ; si l'outil peut maintenant servir à d'autres, le message de partage de la fabrique.

## 5. Quand dire non, ou pas tout de suite

- La demande contredit une règle non négociable (données envoyées à une IA externe, tri de personnes sans avis du DPO, compte partagé sans exception notée) : expliquer, proposer une autre voie.
- L'outil a plus de trois exceptions ouvertes ou un composant sans support : traiter cela d'abord (parcours 4), c'est la condition pour que l'évolution tienne.
- La demande est en fait un autre outil : le dire et repartir avec la fabrique, plutôt que d'alourdir celui-ci.
