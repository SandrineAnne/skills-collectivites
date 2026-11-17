# Livraison

## À chaque version livrée

1. **Le contrôle :** `python3 build/fabriquer.py` doit répondre « tout est cohérent » (tests exécutés et réussis, code sans motif dangereux, versions alignées, aucun secret, aucun appel externe non déclaré, dépendances figées, compose conforme, composants à jour). Pour un outil orange, ajouter `--exiger-analyses`. Sinon, corriger ; ne jamais contourner. Une exception se note dans `docs/derogations.md`.
2. **Le paquet :** `dist/<nom-appli>_vX.Y.Z.zip` et son empreinte `.sha256` (à comparer après tout transfert), fabriqués par le contrôle, sans `.env` ni donnée réelle. C'est la chaîne de fabrication, à redonner pour reprendre le travail dans une nouvelle session. Le fichier HTML (format A), le MSI (format C) ou le dossier `deploy/` (format B) en font partie ou l'accompagnent.
3. **La fiche pour la DSI :** `docs/fiche-dsi.md` (partie automatique remplie ; compléter la partie manuelle, dont la date du dernier essai de restauration).
4. **Le dépôt chez la DSI :** le même contenu, avec l'étiquette `vX.Y.Z`. Lieu en attente de décision (voir `decisions-a-prendre.md`) : tant que ce n'est pas arrêté, demander à la cellule où déposer et l'inscrire dans le README.
5. **La grille définitive** `docs/grille-vigilance.md`, au format de synthèse de la grille (`grille-vigilance.md` de la skill).
6. **La checklist de recette** `docs/recette.md` : un point par critère d'acceptation de la SPEC, coché par le métier, avec date et fonction du testeur.
7. **Le bilan** `dist/bilan-fabrication.md` : réussi, erreurs, alertes, non testé. Il alimente le message de fin.
8. **La fiche du registre** : coller `dist/fiche-registre.txt` dans la carte de l'outil, sur le registre des outils, et la placer dans la bonne colonne (`registre-des-outils.md`).

## Documentation wiki interne (`docs/dokuwiki/`, syntaxe wiki interne)

- **Page utilisateur :** fiche d'identité (nom, version documentée, format, référent et suppléant par fonction, service émetteur, date de mise en service, niveau de la grille, confidentialité), à quoi sert l'outil, usage, FAQ.
- **Page exploitation :** reprend `docs/exploitation.md` : installation, mise à jour, sauvegarde et restauration, retour arrière, supervision, renouvellement des secrets, fin de vie.
- **Page reconstruction :** SPEC complète, architecture, table « fonction du code ↔ RG », jeu de non-régression et résultats attendus, points de vigilance. De quoi redévelopper l'outil ailleurs en cas d'incident.

Chaque page porte « Version documentée : x.y.z ». L'aide de l'application renvoie vers la page utilisateur, qui devient la référence unique.

## Mise en service (format B)

Voir `paquet-integration.md` pour le détail des playbooks et de l'inscription dans la supervision.

1. Déploiement sur le serveur de test (`playbook_deploy.yaml`), contrôle (`playbook_check.yaml`) et recette métier (serveurs : `environnement-collectivite.md`).
2. Validation selon le niveau de la grille : cellule (vert) ; cybersécurité, et DPO si données personnelles (orange) ; DSI et cybersécurité dans tous les cas pour un outil ouvert à l'extérieur. Les exceptions ouvertes de `docs/derogations.md` sont présentées à ce moment-là.
3. Déploiement sur le serveur de production, mêmes contrôles, inscription dans la supervision, essai de sauvegarde puis de restauration, schéma d'infrastructure mis à jour.

## Message de fin

Court et en mots simples (`dialogue-agent.md`) : ce qui est livré · ce que l'agent peut faire maintenant · ce qui a été testé et ce qui ne l'a pas été · niveau du contrôle de sécurité et points restant à traiter · exceptions notées · validations qui n'ont pas eu lieu · prochaine étape proposée · « Ce que j'ai sécurisé pour vous ».
