# Historique

- 0.1.2 (17/11/2026) : la revue des outils (`--controler`) contrôle chaque outil avec le contrôle de la skill, et non plus avec celui qu'il embarque : sans cela, repasser le parc au contrôle après le correctif de sûreté ne changeait rien. Un outil dont le contrôle est antérieur au correctif est « à traiter maintenant ». L'autotest trouve la skill de fabrication aux mêmes endroits que les autres scripts (proposition n° 8, Jorge Bravo).
- 0.1.1 (17/11/2026) : suit le correctif de sûreté de la skill de fabrication (`fabriquer.py` 1.2). La revue des outils signale les dossiers qui embarquent encore l'ancien contrôle : les remettre à niveau et les repasser au contrôle. Un composant noté « plus maintenu » compte comme un support terminé.
- 0.1.0 (17/11/2026) : première version publique, issue d'un premier usage réel dans une collectivité territoriale. Les détails propres à son système d'information ont été retirés ; ce qui dépend de votre organisation se règle dans `environnement-collectivite.md` (skill de fabrication).

## Limites connues

- Pas encore éprouvée sur un vrai incident, ni sur un vrai serveur pour les playbooks fournis ; les essais automatiques passent sur des outils fictifs.
- Les cas d'essai (`evals/evals.json`) décrivent le comportement attendu de Claude ; ils sont à rejouer quand Claude change de version.
- La détection automatique des données réelles ne voit que les numéros de sécurité sociale et les IBAN à clé valide.
