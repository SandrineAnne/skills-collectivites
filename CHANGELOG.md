# Journal des versions

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
