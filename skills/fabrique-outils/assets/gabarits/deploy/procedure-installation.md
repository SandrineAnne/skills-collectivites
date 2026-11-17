# Installer {{TITRE}} sur un serveur

Version documentée : {{VERSION}}

Toujours dans cet ordre : serveur de test, puis serveur de production. Le moteur de conteneurs dépend du serveur : Podman (`podman compose`) ou Docker (`docker compose`) ; les fichiers sont les mêmes.

## Avec Semaphore (recommandé)
1. Sur le serveur : créer `/data/apps/{{NOM}}/.env` à partir de `.env.exemple`, remplacer toutes les valeurs, puis `chmod 600 .env`.
2. Lancer `playbook_deploy.yaml` avec les variables `cible` (hôte) et, si le serveur est sous Docker, `moteur=docker`.
3. Lancer `playbook_check.yaml` avec les mêmes variables.
4. Poser le vhost `{{NOM}}.conf` (emplacement à vérifier avec `nginx -T`), puis `nginx -t` et rechargement. Le playbook le fait si on lance `playbook_deploy.yaml` avec `deploy_vhost=true` (il teste, puis recharge nginx seulement si le vhost a changé) ; sinon, à la main.
5. Inscrire l'application dans la supervision, programmer la sauvegarde, **essayer une restauration** et noter la date dans `docs/fiche-dsi.md`.
6. Mettre à jour le schéma d'infrastructure du serveur.

## À la main
Mêmes étapes : copier `compose.yaml`, `.env.exemple` et `{{NOM}}.conf` dans `/data/apps/{{NOM}}`, créer `.env` (droits 600), puis `podman compose up -d` (ou `docker compose up -d`).

## Retour arrière
L'image précédente est conservée sous l'étiquette `avant-maj` (rejouer la même version ne la déplace pas). Pour revenir : remettre cette étiquette à la place de la version dans `compose.yaml`, relancer `up -d`, puis `playbook_check.yaml`. Si les données ont changé de forme, restaurer la sauvegarde faite avant la mise à jour.
