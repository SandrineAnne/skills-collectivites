# Décisions à prendre dans votre collectivité

La méthode fonctionne avec des valeurs par défaut ; ces points méritent une décision locale. Chaque ligne a un décideur et ce qu'il faut mettre à jour une fois décidé.

| Sujet | Par défaut | Décideur | Une fois décidé |
|---|---|---|---|
| Classes d'outils et délais de remise en marche | `classes-d-outils.md` (classe 1 : le jour même ; 2 : dans la semaine ; 3 : prochaine évolution) | Cellule, puis DSI | Mettre à jour `classes-d-outils.md` et la skill d'entretien |
| Qui entretient un outil | Le chef de projet du progiciel du même domaine | Cellule | Ligne « Chef de projet chargé de l'entretien » du README de chaque outil |
| Responsable du parc d'outils | Une personne de la cellule | Cellule | `roles-et-decisions.md` de la skill d'entretien |
| Porte d'entrée des signalements | Une catégorie « Outils maison » dans l'outil de tickets | DSI | Option `signalement` du module de prise en main |
| Mode d'authentification des applications web | Règles du socle technique, options comparées au premier jalon | DSI, cybersécurité | `socle-technique.md` § 4 |
| Lieu de dépôt du code | Dépôt Git interne de la DSI | DSI | `livraison.md`, `environnement-collectivite.md` |
| Grille de vigilance | Modèle vide fourni : à remplir avec votre cybersécurité avant tout usage | Cybersécurité | `grille-vigilance.md`, puis `scripts/verifier_grille.py` |
| Outils d'analyse sur les postes de fabrication (`pytest`, `ruff`, `bandit`, `pip-audit`, `gitleaks`, `trivy`) | Facultatifs : le contrôle fait ses vérifications intégrées sans eux | DSI | Option `--exiger-analyses` pour les outils sensibles |
| Hébergement des outils ouverts sur Internet | Avis de la DSI et de la cybersécurité avant tout prototype | DSI, cybersécurité | `ouverture-externe.md` |
