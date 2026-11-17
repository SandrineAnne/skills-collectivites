# Historique

- 0.1.1 (17/11/2026) : correctif de sûreté du contrôle (`fabriquer.py` 1.2). Trois défauts signalés par un relecteur : une adresse rangée dans une constante n'était pas vue ; « nosec » sans raison suffisait à lever un refus ; les fichiers d'extension inconnue (`.jsx`, `.tsx`, `.php`, `.sql`, `.pem`) partaient dans le paquet sans être lus. La relecture complète qui a suivi a fermé d'autres contournements du même genre : dossier « vendor », autre encodage, ligne très longue, octets nuls, `window.eval`, adresses en « //hôte », réglages de conteneur dangereux, données de personnes dans un classeur. Le contrôle lit désormais tout ce qui part dans le paquet, la balise de sécurité (CSP) est exigée en format A, et `autotest_surete.py` rejoue 63 cas piégés. Démarrage corrigé sous Python 3.10 et 3.11. Restes de la grille d'origine retirés. **Repasser au contrôle tout outil déjà fabriqué.**
- 0.1.0 (17/11/2026) : première version publique, issue d'un premier usage réel dans une collectivité territoriale. Les détails propres à son système d'information ont été retirés ; ce qui dépend de votre organisation se règle dans `environnement-collectivite.md` (skill de fabrication).

## Limites connues

- Pas encore éprouvée sur un vrai incident, ni sur un vrai serveur pour les playbooks fournis ; les essais automatiques passent sur des outils fictifs.
- Les cas d'essai (`evals/evals.json`) décrivent le comportement attendu de Claude ; ils sont à rejouer quand Claude change de version.
- La détection automatique des données réelles ne voit que les numéros de sécurité sociale et les IBAN à clé valide.
