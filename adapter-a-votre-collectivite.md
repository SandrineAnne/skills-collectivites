# Adapter les skills à votre collectivité

Les skills séparent ce qui est commun (la méthode) de ce qui vous est propre (votre environnement). Comptez une demi-journée pour l’adaptation, avec la DSI.

1. **Votre environnement.** Remplir chaque « [À ADAPTER] » de `skills/fabrique-outils/references/environnement-collectivite.md` : rôles, hébergement, postes, outils d’exploitation.
2. **Votre grille de vigilance.** La grille fournie est un modèle vide : la remplir avec votre cybersécurité (`references/grille-vigilance.md`), puis vérifier la copie avec `scripts/verifier_grille.py`. Sans grille remplie, la skill ne peut pas calculer de niveau vert, orange ou rouge.
3. **Vos adresses et votre réseau.** Les gabarits utilisent `exemple.fr` et le réseau `10.0.0.0/8` : remplacer par vos valeurs (`assets/gabarits/deploy/`, `scripts/creer_projet.py`).
4. **Votre charte graphique.** Le module de prise en main reprend des couleurs à adapter (`assets/prise-en-main/`).
5. **Vos décisions.** Parcourir `references/decisions-a-prendre.md` : classes et délais, qui entretient, porte d’entrée des signalements, lieu de dépôt du code.
6. **Vérifier.** Relancer les essais automatiques, puis essayer la skill sur un petit outil réel, sans donnée de personne.
