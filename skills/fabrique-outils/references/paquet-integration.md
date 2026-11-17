# Paquet d'intégration au système d'information

Objectif : une fois l'outil validé en test, la DSI le pose en production sans rien réinventer, et le retrouve ensuite (supervision, schéma, failles). Le paquet est produit par la skill, pas écrit à la main.

## Ce qui est généré

| Élément | Où | Rôle |
|---|---|---|
| `scripts/creer_projet.py` | skill | crée le dossier du projet avec tous les gabarits (même structure pour tous les outils) |
| `build/fabriquer.py` | copié dans le projet | contrôle le projet et fabrique le paquet `dist/<nom>_vX.Y.Z.zip` seulement si tout colle |
| `deploy/compose.yaml` | format B | gabarit durci (voir socle technique, § 5) |
| `deploy/<nom>.conf` | format B | vhost nginx : réseau interne, en-têtes de sécurité, taille des dépôts |
| `deploy/.env.exemple` | format B | valeurs fictives ; le vrai `.env` est créé sur le serveur (droits 600) |
| `deploy/playbook_deploy.yaml` | format B | déploiement, compatible Semaphore, Podman ou Docker ; n'écrit ni ne lit aucun secret ; attend que l'application réponde |
| `deploy/playbook_check.yaml` | format B | contrôle en lecture seule après déploiement, version en service comprise |
| `deploy/Dockerfile.exemple` | format B | modèle d'image construite sur place (figée, non root) |
| `docs/decisions.md` | tous | choix techniques et leur raison |
| `dist/<nom>_vX.Y.Z.zip.sha256` | tous | empreinte du paquet, à comparer après tout transfert |
| `dist/tests-sortie.txt` | tous | sortie complète des tests exécutés |
| `dist/fiche-registre.txt` | tous | fiche prête à coller dans la carte de l'outil sur le registre des outils (registre du parc) |
| `dist/dossier-transmission.md` | tous | résumé d'une page pour la cellule opérationnelle, avec un statut ; écrit à chaque contrôle, même inachevé |
| `docs/fiche-dsi.md` | tous | fiche de transfert d'une page ; la partie automatique est remplie par `fabriquer.py` |
| `docs/composants.md` | tous | tous les logiciels dont l'outil dépend, avec date de fin de support |
| `docs/derogations.md` | tous | exceptions assumées, avec date de revue |
| `docs/perimetre.md` | tous | ajouts et retraits par rapport à la SPEC validée |
| `dist/bilan-fabrication.md` | tous | résultat des contrôles : réussi, erreurs, alertes, non testé |

## Appeler la cellule tôt, pas à la fin

Le dossier de transmission existe dès le premier contrôle : l'agent peut l'envoyer à la cellule quand il veut, pour un avis, une aide, ou une demande d'installation (statuts et gestes : `partage-et-transmission.md`). Les contrôles ne bloquent que la **fabrication du paquet durable** ; ils n'empêchent jamais de construire ni d'utiliser l'outil.

## Ordre d'emploi

1. **Jalon 1** : `python3 scripts/creer_projet.py <nom> --format A|B|C|D --titre "…"` dès que la SPEC est lancée.
2. **En cours de route** : `python3 build/fabriquer.py --brouillon` pour voir où l'on en est (les champs « À COMPLÉTER » ne bloquent pas).
3. **Jalon 3** : `python3 build/fabriquer.py`. S'il refuse, corriger puis relancer. Ne jamais contourner le contrôle : s'il faut une exception, la noter dans `docs/derogations.md`.
4. **Mise en service (format B)** : donner à la DSI le zip et la fiche. Elle (ou la cellule) lance `playbook_deploy.yaml` depuis Semaphore sur le serveur de test, puis `playbook_check.yaml`, puis recommence en production.

## Mise en service avec Semaphore

- Les playbooks demandent une variable `cible` (hôte de test, puis hôte de production) et, si le serveur est sous Docker, `moteur=docker` (par défaut : `podman`). Les fichiers à poser (`compose.yaml`, vhost, `.env.exemple`) sont pris à côté du playbook : le dossier `deploy/` se dépose tel quel dans votre dépôt Ansible et se lance par une tâche Semaphore ; adapter le nom des groupes d'hôtes à l'inventaire réel.
- Le déploiement attend que l'adresse de santé réponde ; s'il échoue, la procédure de retour arrière est dans `deploy/procedure-installation.md`.
- Aucun secret ne passe par le playbook : s'il manque `/data/apps/<nom>/.env` ou s'il est ouvert à d'autres que root, le déploiement s'arrête avec un message qui dit quoi faire.
- Le vhost n'est posé automatiquement que si `deploy_vhost: true` ; l'emplacement diffère selon le serveur (voir `environnement-collectivite.md`).
- Les contrôles du playbook de vérification : conteneur démarré, redémarrage automatique actif, image avec version précise, port à l'écoute sur 127.0.0.1 seulement, `.env` en 600, réponse locale de l'application, version en service (si `verifier_version=true`), configuration nginx valide.
- Statut : les deux playbooks sont joués de bout en bout par `scripts/essai_playbooks.py` avec un faux moteur de conteneurs (Podman puis Docker), pannes provoquées comprises ; **ils n'ont pas encore tourné sur un vrai serveur**. Au premier usage sur le serveur de test, relire le résultat avec la cellule et corriger les gabarits si besoin.

## Inscription dans la supervision et schéma d'infrastructure

La supervision des conteneurs gère l'état, la relance, la sauvegarde, la restauration, la programmation des sauvegardes et le chef de projet. Après le déploiement :

1. Inscrire l'application dans la supervision du serveur (test ou production), avec son chef de projet.
2. Programmer les sauvegardes et faire un essai de restauration, puis noter sa date dans `docs/fiche-dsi.md`.
3. Mettre à jour le schéma d'infrastructure du serveur : la fiche DSI donne les éléments (conteneurs, versions, adresse, dossier, chef de projet) dans le même format que les cartes du schéma.

## Quand une faille est annoncée

`docs/composants.md` permet de répondre vite à « quels outils sont touchés ? » sans parcourir les serveurs. Les campagnes d'octobre 2026 ont montré l'intérêt d'un double garde-fou : le relevé automatique sur les serveurs (playbooks de contrôle) **et** la liste tenue par chaque outil. Au jalon 3, vérifier les dates de fin de support sur le site de l'éditeur (recherche web), jamais de mémoire.
