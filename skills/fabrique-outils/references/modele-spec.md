# Modèle de SPEC

Deux pages au maximum. Écrire pour la cellule opérationnelle, en langage clair, sans sigle non expliqué (l'agent lit d'abord un résumé en cinq lignes : voir `dialogue-agent.md`) : un agent qui ne connaît pas le projet doit comprendre en cinq minutes ce que fera l'outil. Pour un outil vert et simple, les sections 1, 3, 4, 6, 7 et 8 suffisent.

```markdown
# SPEC — <Nom de l'application> — v<x.y>
Statut : brouillon | validée le JJ/MM/AAAA par la cellule opérationnelle
Source : transcription du JJ/MM/AAAA (<nom du fichier>), anonymisée
Émetteur du besoin : <fonction, service>

> Confidentialité de la source : <anonymisée | contient des noms d'agents, non repris ici, fichier à repasser dans l'outil d'anonymisation>
> Outil existant à rapprocher : <aucun | nom de l'outil et ce qu'il fait déjà>

## 1. Le besoin en une phrase
<La douleur à supprimer, vue par l'utilisateur.>

## 2. Utilisateurs, volumétrie et situation actuelle
- Profils et nombre, aujourd'hui / dans 2 ans (aisance informatique) :
- Ouverture : interne seulement | partenaires identifiés | public | démonstration publique (si autre chose qu'interne : `ouverture-externe.md`) :
- Pourquoi un outil (plutôt que corriger le processus ou demander à l'éditeur) : <une ligne>
- Rustine : non | oui (fiche `docs/rustine.md`)
- Documents produits : aucun | <lesquels, avec la mention de traçabilité>
- Appels vers l'extérieur : aucun | <hôte et raison> (par exemple les tuiles d'un fond de carte ; reporté dans `reseau-autorise.txt`) :
- Fréquence d'usage et pics :
- Volume de données (lignes, fichiers, taille), aujourd'hui / dans 2 ans :
- Situation actuelle chiffrée (temps passé, erreurs, renforts), en précisant si c'est mesuré ou estimé :
- Gain visé et indicateur pour le mesurer :

## 3. Parcours principal
1. … (3 à 7 étapes, vues par l'utilisateur)

## 4. Règles de gestion
- RG-01 — <une règle = une phrase vérifiable>
- RG-02 — …

## 5. Données et logiciels en jeu
- Entrées (formats) :
- Sorties (formats ; un export ouvert est toujours prévu) :
- Stockage : aucun | navigateur (confort seulement) | serveur de la collectivité
- Sensibilité : aucune | interne | personnelle | sensible (santé, social, enfance, RH, finances)
- Logiciels en jeu : <logiciel existant, ce que l'outil remplace ou contourne, mode d'échange : aucun | dépôt de fichiers | import | interface du logiciel> (le mode d'échange compte dans la grille : connexion à un logiciel)

## 6. Format retenu et pourquoi
A | B | C | D — <justification en deux lignes>

## 7. Grille de vigilance provisoire
Niveau : vert | orange | rouge — score X / <score maximal> — points bloquants : …
Engagements de conception pour les points de la grille qui portent sur le code : …
Plan d'actions daté (si orange) : …
Exceptions prévues à une règle du socle (reportées dans `docs/derogations.md`) : aucune | <règle, raison, décideur par fonction, date de revue>

## 8. Critères d'acceptation
- CA-01 (RG-01) — <test que le métier pourra faire en recette>

## 9. Hors périmètre : autres besoins repérés, pistes pour plus tard

## 10. À faire préciser par l'émetteur
- … (5 au maximum ; la cellule décide de recontacter l'émetteur ou de trancher)
```

## Bien écrire les règles de gestion

- Une règle dit ce que fait l'outil, pas comment il est codé : « RG-04 — Un prix qui s'écarte de plus de 10 % du prix de référence est signalé en orange. »
- Elle est vérifiable : un critère d'acceptation peut la tester.
- Elle reprend les mots du métier entendus dans la transcription.
- Une règle supprimée garde son numéro, marquée « supprimée en vX.Y » : les numéros ne sont jamais réattribués, pour que le code et les tests restent lisibles.
