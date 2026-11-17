# Grille de vigilance des outils IA — modèle à remplir

> **Modèle vide.** La grille de vigilance appartient à la cybersécurité de chaque collectivité : aucune grille particulière n'est publiée ici. Remplacez ce modèle par la grille de votre cybersécurité, ou construisez-la avec elle. Ce que la skill attend : une liste de points numérotés « Oui = risque présent », chacun avec un barème ou la mention « Bloquant », un score maximal et trois seuils (vert, orange, rouge).
> **Mise à jour :** à chaque nouvelle version de la grille de votre cybersécurité, remplacer le texte, puis lancer `python3 scripts/verifier_grille.py <fichier de votre cybersécurité>` pour vérifier que la copie intégrée est identique.

L'objectif n'est pas de freiner les projets, mais de repérer ceux qui nécessitent un avis de la cybersécurité ou du DPO. Ton factuel et bienveillant envers les porteurs de projet.

## Déroulé

1. Fiche projet : nom de l'outil, porteur ou service, référent IA, IA utilisée (et type de compte), date d'évaluation.
2. Passer chaque point : Oui / Non / Inconnu, à partir des éléments disponibles (fiche d'une page au premier jalon, code à la livraison). Ne poser des questions que pour les points qui ne se déduisent pas.
3. Sur du code, vérifier concrètement les points qui portent sur le code : secrets, appels à des IA externes et données envoyées, authentification, mots de passe, traçabilité.
4. Calculer le score et le niveau, puis rendre la synthèse.

## Les points (Oui = risque présent)

Une ligne par point, au format ci-dessous : `scripts/verifier_grille.py` lit ce tableau.

| # | Thème | Point | Points |
|---|---|---|---|
| 1 | [À REMPLIR] | [À REMPLIR] | [barème ou « Bloquant (n) »] |
| 2 | [À REMPLIR] | [À REMPLIR] | [barème ou « Bloquant (n) »] |
| 3 | [À REMPLIR] | [À REMPLIR] | [barème ou « Bloquant (n) »] |

Sujets qu'une grille de ce type couvre généralement, à faire trancher par votre cybersécurité (liste indicative, sans numéro ni barème) :

- **Architecture et hébergement :** stockage de données ; connexion à un logiciel métier, à l'annuaire ou à la messagerie ; accès depuis Internet ; hébergement hors du système d'information.
- **Données :** données personnelles ; données sensibles (santé, social, enfance, ressources humaines, finances) ; avis du DPO.
- **Intelligence artificielle :** envoi de données à une IA externe ; décisions concernant des personnes ; résultats non vérifiés par un humain.
- **Code et accès :** secrets écrits dans le code ; code généré ni relu ni analysé ; authentification ; mots de passe et comptes partagés ; traçabilité.
- **Maintenance :** une seule personne capable de maintenir l'outil ; documentation et copie du code remise à la DSI.

## Calcul du niveau

- Score = somme des points des réponses « Oui ». Score maximal : [À REMPLIR].
- **Vert :** [À REMPLIR] et aucun point bloquant. Validation possible par le référent IA.
- **Orange :** [À REMPLIR] et aucun point bloquant. Avis de la cybersécurité requis, et du DPO si des données personnelles sont traitées.
- **Rouge :** [À REMPLIR], ou au moins un point bloquant. Mise en production bloquée jusqu'à correction.
- Réponses « Inconnu » : ne pas les compter dans le score, mais les lister et préciser le niveau atteint si elles s'avéraient « Oui ». Si un point bloquant est inconnu, indiquer « Niveau provisoire ».

## Format de la synthèse

```
GRILLE DE VIGILANCE IA
Outil : …
Porteur / service : …
Référent IA : …
IA utilisée : …
Date : …

Niveau : Vert / Orange / Rouge
Score : X / [score maximal] · N point(s) bloquant(s)
Suite à donner : …

Points relevés :
- [BLOQUANT] …
- …

Points à vérifier (réponse inconnue) :
- …

Actions recommandées :
1. … (action concrète, la plus urgente d'abord)
```

Rappeler en une ligne que la grille est une aide à la décision et ne remplace pas l'avis de la cybersécurité ou du DPO pour les niveaux orange et rouge.

## Usage dans la fabrique (propre à cette skill)

- **Premier jalon (fiche d'une page) :** remplir la fiche et passer les points à partir de la fiche : niveau provisoire. Les points qui portent sur le code ne peuvent pas encore être vérifiés : la fiche s'engage à les éviter.
- **Livraison :** grille définitive, écrite dans `docs/grille-vigilance.md` avec fichiers et lignes cités.
- **Point bloquant inconnu au premier jalon** (typiquement l'avis du DPO) : niveau provisoire ; demander l'avis avant toute donnée réelle.
- **Données de développement :** développer avec Claude sur des données fictives ou anonymisées n'est pas un envoi de données à une IA externe ; l'outil en service, lui, ne doit en envoyer aucune sans l'accord prévu par votre grille.
- **Outil ouvert à l'extérieur :** le point sur l'accès depuis Internet s'applique ; voir `ouverture-externe.md`.
- **Réévaluation :** à chaque évolution importante (nouvelle donnée, nouvel accès, nouvelle connexion, ouverture à d'autres publics).
