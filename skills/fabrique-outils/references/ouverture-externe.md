# Outil ouvert à des utilisateurs extérieurs

À lire dès que la SPEC prévoit des utilisateurs hors de la collectivité (communes, intercommunalités, élus, partenaires, usagers) ou une diffusion publique (LinkedIn, rencontre des maires, partage du code).

L'outil est interne par défaut. Ouvrir à l'extérieur est une décision explicite, inscrite dans la SPEC (section 2, « Ouverture ») et validée **avant le prototype**, car elle change le format, l'hébergement, l'authentification et le niveau de la grille.

## Trois cas

| Cas | Exemples | Ce qui change |
|---|---|---|
| **1. Démonstration publique** | carte HTML montrée sur LinkedIn, démonstration sur un stand | Fichier HTML autonome, sans donnée réelle ni nominative, sans secret ni nom de serveur interne, relu avant diffusion. C'est la diffusion d'un document, pas un service : l'outil en service reste interne. Le partage du code suit la même revue, avec l'accord de la direction concernée |
| **2. Outil pour des partenaires identifiés** | communes ou intercommunalités avec un compte, élus | Application web accessible depuis Internet : point « accessible depuis Internet » de la grille au minimum ; hébergement et protection à décider avec la DSI et la cybersécurité ; comptes nominatifs pour les externes ; journal ; support |
| **3. Service au public** | formulaire ou portail pour des usagers | Ne pas démarrer avec cette skill seule : avis préalable de la DSI, de la cybersécurité, du DPO et de la direction concernée, puis cadrage dédié |

## Questions à inscrire dans la SPEC (section 2 et section 10)

1. Qui exactement (catégories, nombre) et comment sont-ils identifiés ?
2. Quelles données voient-ils, lesquelles saisissent-ils ? Y a-t-il des données personnelles ?
3. Qui héberge et expose l'outil ? La skill ne choisit pas : question à poser à la DSI et à la cybersécurité.
4. Qui assure le support, à quels horaires, et que se passe-t-il en cas de panne ou d'incident ?
5. Mentions légales, information RGPD, durée de conservation, obligations d'accessibilité numérique : à vérifier avec le DPO et la DSI.
6. Comment un utilisateur externe perd-il son accès (départ, changement de poste) ? Qui peut couper l'accès en urgence, et comment ?

## Effets sur la grille

- Accessible depuis Internet : toujours compté.
- Hébergé hors du SI : à éviter, voir ci-dessus.
- Authentification, mots de passe, traçabilité : des comptes externes obligent à une authentification solide et à un journal ; l'absence d'authentification sur des données est bloquante.
- Règle de la skill : une ouverture à des externes est signalée à la cellule **même si le score reste vert**, et la mise en service demande l'avis de la DSI et de la cybersécurité (et du DPO si des données personnelles sont traitées). La cellule seule ne valide pas un outil ouvert à l'extérieur.

## Conception en plus

- Aucune ressource tierce chargée chez le visiteur (polices, scripts, statistiques, CDN) : ni suivi, ni dépendance.
- Limitation du nombre de tentatives de connexion, taille et type des dépôts contrôlés, messages d'erreur sans détail technique.
- Tutoriel sans jargon interne ni nom d'agent ; contact du support dans le chapitre « À propos » du guide.
- Procédure d'arrêt d'urgence écrite dans la page d'exploitation, avec la fonction de la personne qui peut l'exécuter.
