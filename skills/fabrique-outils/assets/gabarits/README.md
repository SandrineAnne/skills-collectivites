# {{TITRE}}

Version : {{VERSION}}
Format : {{FORMAT}}
Niveau : {{NIVEAU}}
Classe : À COMPLÉTER (1 essentiel, 2 important, 3 confort ; fixée par la cellule opérationnelle)
Créé le : {{DATE}}

> Ce fichier est la carte d'identité de l'outil. Tout agent de la collectivité doit pouvoir, avec ce dossier seul, comprendre l'outil, le réinstaller et le mettre à jour, sans l'aide de Claude.

## À quoi sert l'outil
À COMPLÉTER : une ou deux phrases, avec les mots du métier.

## Qui s'en occupe
- Référent (fonction) : À COMPLÉTER
- Suppléant (fonction) : À COMPLÉTER
- Service demandeur : À COMPLÉTER
- Chef de projet chargé de l'entretien (fonction) : À COMPLÉTER
- Où le trouver (adresse ou lieu de téléchargement) : {{OU_TROUVER}}
- Documentation (page du wiki) : À COMPLÉTER
- Niveau du contrôle de sécurité (vert, orange, rouge) : À COMPLÉTER

## Démarrer en 5 minutes
À COMPLÉTER : les étapes pour ouvrir ou installer l'outil, vues par un agent non informaticien.

## Où est quoi
- `SPEC.md` : ce que fait l'outil et ses règles (RG-01, RG-02…). C'est la référence.
- `CHANGELOG.md` : ce qui a changé à chaque version.
- `src/` : le code (`src/coeur/` : les règles métier).
- `tests/` : les exemples inventés et les résultats attendus.
- `docs/` : fiche pour la DSI, contrôle de sécurité, recette, exploitation, composants, décisions techniques, exceptions, périmètre, partage et transmission, journal des incidents.
- `deploy/` : ce qu'il faut poser sur le serveur (outils web uniquement).
- `build/fabriquer.py` : contrôle le dossier et fabrique le paquet à livrer.

## Reconstruire ou mettre à jour
1. Modifier la SPEC d'abord (règle ajoutée ou changée), puis le code, puis un test.
2. Mettre à jour `VERSION` et `CHANGELOG.md`.
3. Lancer `python3 build/fabriquer.py` : il exécute les tests, contrôle le code, les secrets, les dépendances et la documentation, refuse de fabriquer le paquet si quelque chose ne colle pas, et dit quoi corriger (`--help` pour les options).
4. Un défaut corrigé = un test ajouté dans `tests/`.

## Dépôt du code
À COMPLÉTER : où le code est déposé chez la DSI (à chaque version).
