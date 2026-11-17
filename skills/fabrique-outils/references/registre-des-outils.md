# Le registre du parc : le registre des outils

Le tableau de l'espace registre « Usages et accompagnement des cas d'usages » est le registre officiel des outils : une carte par outil, qui avance de colonne en colonne au fil de sa vie. Les deux skills (fabrication et entretien) s'y raccrochent.

## Colonnes et étapes des skills

| Colonne du tableau | Étape | Geste attendu sur la carte |
|---|---|---|
| Colonne d'entrée (besoins) | Étape 0 de la fabrique, signalement de trois lignes | Créer la carte : nom, service, besoin en une phrase |
| Premier prototype présenté | Jalon 2 | Joindre la fiche d'une page validée |
| Phase de test | Jalon 3 et recette, serveur de test | Coller la fiche du registre produite par le contrôle |
| Déploiement | Mise en service en cours | Fiche à jour, classe fixée, dossier déposé |
| En service *(colonne proposée)* | Entretien | Fiche mise à jour à chaque version, incident clos ou revue |
| Retirés *(colonne proposée)* ou Cas d'usages abandonnés | Fin de vie | Noter la date de retrait, l'effacement des données et l'archivage du dossier |

## Fiche automatique (outils maison)

À chaque contrôle, `build/fabriquer.py` écrit `dist/fiche-registre.txt` : un texte prêt à coller dans la carte, rempli à partir du dossier (README, composants, exceptions, partage, statut du contrôle). Ce qui manque y apparaît « à compléter » : on le complète dans le README, pas dans la carte, pour que le dossier reste la référence.

## Fiche type à remplir à la main

Pour un outil sans dossier, un assistant Claude ou une solution externe, copier ce modèle dans la description de la carte :

```
Outil :
Nature : outil maison | assistant Claude | solution externe
À quoi il sert :
Service demandeur :
Classe : 1 essentiel | 2 important | 3 confort
Référent métier :
Suppléant :
Chef de projet chargé de l'entretien :
Où le trouver (adresse, lieu de téléchargement ou projet Claude) :
Version en service :
Dossier (code et documentation) :
Documentation :
Contrôle de sécurité (grille de vigilance) :
Données de personnes : non | oui (avis du DPO du …, inscrit au registre des traitements)
Dernière revue :
Prochaine revue :
Réutilisable par d'autres : oui | non
Rustine : non | oui — problème de fond : … (appartient à : …)
Fonction d'IA : non | oui — questions-tests rejouées le …
```

Lignes à ajouter selon la nature :
- **assistant Claude** : « Documents de référence à jour au : … » et « Questions-tests repassées le : … (résultat) » ;
- **solution externe** : « Éditeur et contrat jusqu'au : … » et « Interlocuteur chez l'éditeur : … (fonction) ».

## Trois natures, trois entretiens

| Nature | Exemples | Entretien |
|---|---|---|
| Outil maison | Vérificateur de frais de repas, revue de presse, renommage de fichiers | Les deux skills : dossier, contrôle, skill d'entretien |
| Assistant Claude | Espace documentaire et rédaction | Hors des skills : documents de référence à jour, questions-tests repassées chaque année, consignes revues quand Claude change |
| Solution externe | Service de transcription en ligne | Hors des skills : contrat, éditeur, versions, réversibilité des données |
