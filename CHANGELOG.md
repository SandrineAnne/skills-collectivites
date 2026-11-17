# Journal des versions

## 0.1.2 — revue des outils et contributions

- **Revue des outils (`entretien-outils`).** Avec `--controler`, la revue contrôlait chaque outil avec le contrôle qu’il embarque, c’est-à-dire l’ancien : repasser le parc au contrôle après le correctif de la 0.1.1 ne changeait rien. Elle utilise désormais le contrôle de la skill, et place en « à traiter maintenant » tout outil dont le contrôle est antérieur au correctif.
- **Mode essai** tant que la skill n’est pas adaptée : aucun niveau ni score annoncé sans grille remplie (n° 7).
- **Module de prise en main plus accessible** : contour de focus lisible dans les deux thèmes, bulle entière à fort zoom, focus rendu à la fermeture (n° 9).
- **Playbooks** : santé du conteneur vérifiée, étiquette de retour arrière conservée, nginx rechargé seulement si le vhost a changé et s’il est valide (n° 10).
- L’autotest de l’entretien trouve la skill de fabrication aux mêmes endroits que les autres scripts (n° 8).

Merci à Jorge Bravo pour les propositions n° 7 à 10.

## 0.1.1 — correctif de sûreté

**À installer à la place de la 0.1.0, puis repasser au contrôle tout outil déjà fabriqué.**

- **Contrôle `fabriquer.py` 1.2.** Trois défauts signalés en privé, selon `SECURITY.md` : une adresse rangée dans une constante n’était pas vue ; « nosec » sans raison suffisait à lever un refus ; les fichiers d’extension inconnue (`.jsx`, `.tsx`, `.php`, `.sql`, `.pem`) partaient dans le paquet sans être lus.
- **Relecture complète du contrôle.** Il lit désormais tout ce qui part dans le paquet, quels que soient l’extension, l’encodage, le dossier ou la longueur des lignes ; ce qu’il ne peut pas lire est nommé dans le bilan. Toute adresse écrite dans le code doit être déclarée ; une adresse construite à l’exécution est refusée ; la balise de sécurité (CSP) est exigée en format A ; chaque exemption est motivée et recopiée au bilan ; les réglages de conteneur qui donnent la main sur le serveur sont refusés ; les données de personnes sont cherchées aussi dans les classeurs.
- **`autotest_surete.py` :** 63 cas piégés, un par contournement connu.
- **Démarrage sous Python 3.10 et 3.11** (proposition n° 1), **restes de la grille d’origine retirés** (n° 2), **composant « plus maintenu » compté comme un support terminé** (n° 3). Merci à Jorge Bravo pour ces trois propositions et pour sa relecture.
- Le contrôle dit maintenant ce qu’il ne garantit pas : il cherche des défauts connus, il ne prouve pas leur absence.

## 0.1.0 — première ébauche publique

- `fabrique-outils` et `entretien-outils`, deux skills génériques issues d’un premier usage au Département du Loiret (novembre 2026).
- Aucune référence à une organisation particulière dans les skills ; l’environnement se décrit dans `environnement-collectivite.md`.
- Grille de vigilance livrée comme modèle vide, à remplir avec votre cybersécurité.
- Grille de vigilance fournie comme modèle vide ; la skill y renvoie par thème, plus par numéro de point.
- Essais automatiques : 130 contrôles pour la fabrique, 47 pour l’entretien, sur des outils fictifs.
