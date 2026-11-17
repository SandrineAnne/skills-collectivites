# Contrat d'entrée — {{TITRE}}

Version documentée : {{VERSION}}

Chaque fichier que l'outil reçoit d'ailleurs (trame d'une agence, export d'un logiciel, tableau d'un service) est décrit ici, avec un exemple inventé dans `tests/donnees/`. Quand une source change de format, on ajoute une ligne et un exemple : l'outil reconnaît la nouvelle version, ou dit clairement qu'il ne la connaît pas (brique « reconnaître une trame »). Claude tient ce tableau ; l'agent n'a rien à écrire. Un outil qui ne lit aucun fichier laisse le tableau vide.

| Entrée | Produite par | Format attendu (version, colonnes clés) | Fichier exemple | Si le format change |
|---|---|---|---|---|
