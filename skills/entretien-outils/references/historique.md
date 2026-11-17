# Historique

- 0.1.0 (17/11/2026) : première version publique, issue d'un premier usage réel dans une collectivité territoriale. Les détails propres à son système d'information ont été retirés ; ce qui dépend de votre organisation se règle dans `environnement-collectivite.md` (skill de fabrication).

## Limites connues

- Pas encore éprouvée sur un vrai incident, ni sur un vrai serveur pour les playbooks fournis ; les essais automatiques passent sur des outils fictifs.
- Les cas d'essai (`evals/evals.json`) décrivent le comportement attendu de Claude ; ils sont à rejouer quand Claude change de version.
- La détection automatique des données réelles ne voit que les numéros de sécurité sociale et les IBAN à clé valide.
