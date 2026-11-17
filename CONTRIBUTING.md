# Contribuer

Merci de votre intérêt. Trois façons d’aider, de la plus simple à la plus technique.

## 1. Raconter un essai

Ouvrez un ticket « Retour d’essai » : quel outil vous avez fabriqué ou entretenu, à quel niveau du curseur, ce qui a aidé, ce qui a freiné, ce que Claude a mal compris. Un retour d’essai vaut autant qu’une correction.

## 2. Signaler un problème

Ouvrez un ticket « Problème » avec ce qui s’est passé, ce que vous attendiez, et la version de la skill. **Ne collez jamais de données réelles** (noms, numéros, documents d’usagers) ni de détail de votre système d’information.

## 3. Proposer une amélioration

1. Une modification à la fois, expliquée en mots simples.
2. Les essais automatiques passent :
   ```bash
   python3 skills/fabrique-outils/scripts/autotest_fabrique.py
   python3 skills/fabrique-outils/scripts/autotest_surete.py
   python3 skills/entretien-outils/scripts/autotest_entretien.py
   ```
3. Une règle ajoutée a son essai. Un contournement du contrôle devient une ligne de `autotest_surete.py`. Une règle qui ralentirait l’agent qui crée doit être appliquée par Claude, ou n’être exigée qu’à l’installation : c’est la règle d’or des skills.
4. Rien de propre à votre organisation dans les fichiers communs : cela va dans `environnement-collectivite.md`.

En proposant une contribution, vous acceptez qu’elle soit diffusée sous la licence EUPL 1.2 du dépôt.
