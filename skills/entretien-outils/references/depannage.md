# Parcours 1 — Dépannage

Ordre immuable : **trier → stabiliser → diagnostiquer → corriger → clore.** On ne corrige jamais avant d'avoir remis en marche ce qui peut l'être, et on ne clôt jamais sans test ajouté.

## 1. Trier (en mots simples, une question à la fois)

Le signalement arrive par un ticket (catégorie « Outils maison », quand elle existera) ou par le référent. Avant toute question, lire la fiche du registre ou le README de l'outil : sa **classe**, son chef de projet, son mode dégradé. Pour un outil de **classe 1**, donner tout de suite aux agents le mode dégradé (`docs/mode-degrade.md`) : ils continuent de travailler pendant qu'on répare.

1. « Est-ce que des personnes sont bloquées en ce moment ? Combien à peu près ? » → gravité (bloquant, gênant, mineur).
2. « Depuis quand ? Qu'est-ce qui a changé juste avant : une mise à jour de l'outil, un nouveau fichier, un autre poste ou navigateur, un redémarrage du serveur ? » → la cause est très souvent le dernier changement.
3. « Le problème touche-t-il tout le monde, ou une seule personne, un seul poste, un seul fichier ? » → outil ou environnement.
4. « Des données de personnes ont-elles pu être vues par qui ne devait pas, perdues ou modifiées ? » → si oui ou si doute : DPO sans attendre (72 heures pour notifier une violation à la CNIL), cybersécurité en cas de soupçon d'attaque.

Puis ouvrir le dossier de l'outil : `README.md` (format, référent), `CHANGELOG.md` (dernière version et ce qu'elle a changé), `docs/incidents.md` (le problème est-il déjà arrivé ?). Pas de dossier : terminer le dépannage, puis enchaîner sur le parcours 2.

## 2. Stabiliser : revenir à ce qui marchait

| Format | Retour arrière | Qui le fait |
|---|---|---|
| A. Fichier HTML | Rediffuser le fichier de la version précédente (paquet `dist/` de cette version, dépôt chez la DSI, ou copie conservée par le référent) ; prévenir les utilisateurs de ne plus ouvrir l'ancien | Référent |
| B. Application web | Remettre l'image étiquetée `avant-maj` dans `compose.yaml`, relancer, puis `playbook_check.yaml` (`deploy/procedure-installation.md`) ; si les données sont abîmées : restaurer la sauvegarde d'avant la mise à jour depuis la supervision | Cellule ou DSI |
| C. Programme installé (MSI) | Réinstaller le MSI de la version précédente sur les postes touchés | Référent avec le support informatique |
| D. Grist | Restaurer une sauvegarde ou une version précédente du document, si l'historique est activé ; sinon corriger la formule ou la colonne en cause sur une copie | Référent du document |

Si aucun retour arrière n'est possible (pas de version précédente conservée) : le noter, proposer un contournement simple aux utilisateurs (« en attendant, faites ainsi »), puis diagnostiquer. C'est aussi un enseignement à inscrire au journal.

## 3. Diagnostiquer

Rassembler les faits avant toute hypothèse :
- la **version en service** (chapitre « À propos » du tutoriel, adresse `/sante`, étiquette de l'image) et ce que la dernière version a changé ;
- le **message exact** (capture d'écran sans donnée de personne, ou texte recopié) ;
- les **journaux** : console du navigateur (touche F12, onglet Console) pour un fichier HTML ; `podman logs --since 2h <conteneur>` ou `docker logs`, journal applicatif et supervision pour une application web ; observateur d'événements Windows pour un MSI ;
- pour une application web : relancer `playbook_check.yaml` (état, redémarrage automatique, port, santé, version).

Reproduire ensuite le défaut **sur des données inventées ou anonymisées** : jamais le fichier réel d'un usager dans la conversation.

### Symptômes fréquents et premières pistes

| Symptôme | Pistes, dans l'ordre |
|---|---|
| Page blanche ou bouton sans effet (format A) | Erreur dans la console (F12) ; fichier ouvert depuis l'aperçu de la messagerie au lieu d'être enregistré puis ouvert ; fichier tronqué ou modifié pendant un envoi ; navigateur ancien ; stockage du navigateur plein ou bloqué |
| « Fichier non reconnu », colonnes introuvables | Une nouvelle trame ou un nouvel export : comparer à `docs/entrees.md` et à ses exemples, puis parcours évolution (nouvel exemple, nouvelle version reconnue) et signalement au propriétaire noté dans la fiche rustine. Sinon, la source a changé : colonne renommée, export modifié par le logiciel d'origine, feuille ou lignes masquées, filtre actif ; séparateur du CSV (point-virgule ou virgule) ; encodage (accents cassés) ; fichier trop gros |
| Chiffres faux ou différents d'avant | Source modifiée ou incomplète ; lignes masquées ou filtres ; arrondis ; règle de gestion mal comprise ou changée → refaire le rapprochement avec la source, au centime |
| « Bad Gateway » (502) ou « Service indisponible » (format B) | Conteneur arrêté ou qui redémarre en boucle (santé en échec) ; mémoire insuffisante (processus tué par le système) ; disque plein ; port ou vhost modifié |
| « Accès refusé » (403) | Connexion depuis l'extérieur du réseau interne ou hors VPN ; compte désactivé ou droits retirés ; portail d'authentification en panne |
| Avertissement de sécurité du navigateur | Certificat expiré ou mal renouvelé |
| Ne repart pas après un redémarrage du serveur | Redémarrage automatique absent (`restart: always`) ; dossier des données déplacé ou non monté |
| Très lent | Volume de données au-delà de ce qui était prévu dans la SPEC ; mémoire ; base de données à entretenir ; requête qui relit tout |
| Programme installé qui ne s'ouvre plus (format C) | Antivirus ou mise à jour Windows ; droits du poste ; dépendance manquante (OCR, modèle) ; chemin réseau indisponible |
| Juste après une mise à jour de l'outil | C'est une régression : retour arrière d'abord, puis comparaison des deux versions |

## 4. Corriger

1. Écrire le **test qui reproduit le défaut** et vérifier qu'il échoue.
2. Faire la **correction la plus petite possible** ; pas d'amélioration opportuniste pendant un dépannage (elle ira dans une évolution).
3. Lancer **tous les tests** : la correction ne doit rien casser ailleurs.
4. `python3 scripts/nouvelle_version.py <dossier> correction "Ce qui est corrigé, en mots simples"`.
5. `python3 build/fabriquer.py` : il doit passer comme pour une livraison.
6. Serveur de test, puis production (format B : `playbook_deploy.yaml` puis `playbook_check.yaml`), par une personne habilitée.

**Urgence réelle sans retour arrière possible** : correction minimale tout de suite, avec le test si c'est faisable ; chaque étape sautée est notée dans `docs/derogations.md` avec une date de régularisation proche (une semaine).

## 5. Clore

- **Journal** : une ligne dans `docs/incidents.md` le jour même — date, gravité, ce qui s'est passé, cause, correction et version, test ajouté, statut. Sans donnée de personne, sans nom de personne, sans reproche.
- **Retour d'expérience** (incident bloquant) : cinq lignes sous le tableau — ce qui s'est passé, pourquoi on ne l'a pas vu venir, ce qui a bien marché, ce qu'on change (souvent : un contrôle, un test, une alerte de la supervision), qui le fait et pour quand.
- **Message aux utilisateurs** : court, sans jargon (modèles dans `dialogue-entretien.md`).
- **Fiche du registre** : recoller la fiche `dist/fiche-registre.txt` (nouvelle version, date du contrôle).
- **Ticket** : noter son numéro dans la ligne du journal des incidents (« Ce qui s'est passé »), puis le faire clore.
- **Récurrence** : un même incident deux fois = une évolution à prévoir (parcours 3), pas un troisième dépannage.
