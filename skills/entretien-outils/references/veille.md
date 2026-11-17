# Parcours 4 — Veille

Un outil vieillit même quand personne n'y touche : ses composants perdent leur support, des failles sont publiées, les sauvegardes ne sont plus essayées, le référent change de poste. La veille repère cela **avant** l'incident.

## Le calendrier d'entretien

| Rythme | Quoi | Qui |
|---|---|---|
| Chaque trimestre | Revue automatique de tous les outils (`veille_outils.py`) | Responsable du parc |
| Chaque semestre | Outils de classe 1 : restauration, composants, mode dégradé essayé, usage | Cellule, chefs de projet, référents |
| Une fois par an | Journée d'entretien : chaque outil passe par cette skill ; revue du parc | Cellule, référents, DSI |
| À tout moment | Faille annoncée : `veille_outils.py --chercher` | Cellule, DSI, cybersécurité |

La revue signale aussi : un outil **sans classe**, un outil de **classe 1** resté au niveau partagé, sans mode dégradé ou sans suppléant, et un dossier dont le **contrôle embarqué est ancien** (à mettre à jour avec `remettre_a_niveau.py --mettre-a-jour-fabriquer` pour qu'il profite des dernières règles de sûreté).

**Après un correctif du contrôle** (une nouvelle version de `fabriquer.py`), remettre chaque dossier à niveau (`remettre_a_niveau.py --mettre-a-jour-fabriquer`) et le repasser au contrôle : un outil accepté par l'ancien contrôle peut être refusé par le nouveau, et c'est justement ce qu'on cherche. La revue le fait d'un coup : `veille_outils.py <parc> --controler --fabrique <skill fabrique-outils>` contrôle chaque outil avec le contrôle de la skill, jamais avec celui qu'il embarque, et place en « à traiter maintenant » tout outil dont le contrôle est antérieur au correctif de sûreté (1.2).

## La revue trimestrielle

`python3 scripts/veille_outils.py <dossier contenant les outils> [--controler] [--sortie revue.md]`

Pour chaque outil qui a un dossier (README et VERSION), le script lit :
- `docs/composants.md` : support terminé (à traiter maintenant), fin dans moins de 6 mois (à planifier), date absente ou illisible ;
- `docs/incidents.md` : incidents encore ouverts ;
- `docs/derogations.md` : exceptions dont la date de revue est dépassée ;
- `docs/fiche-dsi.md` : essai de restauration jamais fait ou de plus d'un an (format B) ;
- le README : référent indiqué ou non ;
- avec `--controler` : lance le `build/fabriquer.py` de chaque outil (contrôle complet, sans paquet) et signale ceux qui échouent.

Le rapport classe les outils en **à traiter maintenant**, **à planifier** et **en ordre**. Le code de sortie vaut 1 s'il y a quelque chose à traiter maintenant : une tâche programmée peut ne prévenir que dans ce cas.

Après la revue, la date de « Dernière revue » est reportée sur chaque carte du registre des outils ; un outil du tableau sans dossier repérable par la revue est un outil à reprendre (parcours 2).

Dates de fin de support : `veille_outils.py` lit celles du dossier. Les vérifier une fois par an sur le site des éditeurs (recherche en ligne), et à chaque évolution.

## La revue du parc (journée annuelle)

Au-delà des contrôles, la journée annuelle décide pour chaque outil : **garder**, **mutualiser** (un autre outil fait la même chose), **retirer** (plus utilisé, ou rustine devenue inutile) ou **remonter au processus** (le problème de fond mérite d'être corrigé à la source : agence, éditeur, organisation). Le rapport de `veille_outils.py` compte les rustines et signale celles dont la revue est dépassée, ainsi que les questions-tests d'IA à rejouer. Les décisions sont reportées sur les cartes du registre des outils.

## Quand une faille est annoncée

1. `python3 scripts/veille_outils.py <dossier des outils> --chercher <composant>` (par exemple `php`, `node`, `brotli`, `nginx`) : liste les outils dont les composants, dépendances ou images mentionnent ce nom.
2. Pour chacun : version concernée ? exposée sur le réseau ? Si oui, une correction (parcours 3, version x.y.z) : mise à jour du composant, tests, `fabriquer.py`, test puis production.
3. Croiser avec les relevés automatiques sur les serveurs (playbooks de contrôle de l'exploitation) : la liste des outils et le relevé des serveurs se complètent.

## En tâche programmée (facultatif)

Une tâche programmée trimestrielle peut lancer la revue et envoyer le rapport à la cellule. Exemple de consigne :

> Lance `python3 <chemin de la skill>/scripts/veille_outils.py <dossier des outils> --controler --sortie revue-outils.md`. Si le code de sortie vaut 1, envoie à la cellule opérationnelle le contenu de la rubrique « À traiter maintenant », en trois lignes par outil, sans aucune donnée de personne. Sinon, envoie une ligne : « Revue trimestrielle des outils : rien à traiter. »

## Ce qui relève aussi de la veille

- **Référent parti ou suppléant absent** : le signaler à la cellule ; un outil sans référent est un outil orphelin (parcours 2).
- **Outil plus utilisé** : proposer la fin de vie plutôt que de l'entretenir pour rien.
- **Mesure du gain** : à trois mois de la mise en service, l'indicateur de la SPEC a-t-il été mesuré ? (voir la fabrique, socle technique, § 6).
