# Fiche d'observation — test de la skill

À utiliser quand la cellule teste la skill sur un besoin réel. Elle sert à la faire évoluer, pas à évaluer les personnes. Claude la tient à jour pendant le test et la remet à la fin ; la cellule corrige et complète.

## Avant le test (cellule)

- Besoin choisi (en une phrase) et format attendu (A, B, C, D) :
- Transcription disponible et anonymisée : oui / non
- Grille de la cybersécurité : intégrée à la skill (version du JJ/MM/AAAA)
- Résultat attendu à la fin du test (SPEC seule, prototype, outil livré) :

## À chaque jalon (Claude remplit, la cellule corrige)

| | Jalon 1 · SPEC | Jalon 2 · prototype | Jalon 3 · livraison |
|---|---|---|---|
| Durée (de la demande à l'accord) | | | |
| Nombre d'aller-retours avant validation | | | |
| Questions posées par Claude qui n'apportaient rien | | | |
| Ce qui manquait (information, modèle, règle) | | | |
| Ce qui a gêné ou ralenti | | | |
| Ce qui a bien marché | | | |

## Points précis à regarder

- **Étape 0 :** la skill a-t-elle lu l'environnement, signalé les noms résiduels, repéré les autres besoins, proposé un outil existant à rapprocher ?
- **SPEC :** tient-elle en 2 pages ? La cellule l'a-t-elle comprise sans explication ? Les règles de gestion sont-elles testables ?
- **Grille :** niveau provisoire et niveau définitif identiques ? Un point mal compris ?
- **Jalons :** trop nombreux, trop rares, ou bien proportionnés au niveau ?
- **Prototype :** données fictives réalistes ? Parcours reconnu par l'émetteur du besoin ?
- **Tutoriel :** visite lancée sans retouche du module ? Textes compris sans explication ?
- **Documentation et versions :** une version unique partout ? Page de reconstruction exploitable par quelqu'un qui n'a pas vu le projet ?
- **Reprise :** après la fermeture de la session, le dossier du projet suffit-il à reprendre le travail ?

## Déclenchement et partage

- La skill s'est-elle déclenchée au bon niveau du curseur ? Une demande « jetable » l'a-t-elle alourdie ? Une demande « partagée » est-elle passée sans garde-fous ?
- Le message sur le partage est-il venu au bon moment, une seule fois, et a-t-il été bien reçu (sourire, agacement) ?
- L'outil a-t-il été signalé à la cellule ? Un exercice de reprise a-t-il eu lieu ?

## Lisibilité pour l'agent qui fabrique (à regarder à chaque jalon)

- L'agent a-t-il compris **chaque question sans explication** ? Lesquelles ont dû être reformulées ?
- Combien de questions par message ? Chacune avait-elle sa raison et sa proposition ?
- Y avait-il un terme technique non expliqué (sigle, « SPEC », « format B », « dérogation »…) ?
- L'agent a-t-il répondu « je ne sais pas » ? La skill a-t-elle continué avec une hypothèse notée ?
- Les garde-fous ont-ils été vécus comme une aide ou comme un refus ?
- Le message de fin, y compris « Ce que j'ai sécurisé pour vous », a-t-il été compris ?

## Temps et fabrication

- Durée de chaque étape et nombre de questions posées à l'agent.
- `fabriquer.py` : combien de passages avant un résultat propre ? Quelle erreur est revenue le plus souvent ?
- Mise en service (format B) : les playbooks ont-ils tourné sans retouche sur le serveur de test ?

## Bilan (cellule)

- La méthode a-t-elle alourdi ou allégé le travail, par rapport à la façon habituelle ?
- Une étape à supprimer ? Une étape manquante ?
- Un message de la skill qui a surpris ou agacé ?
- Prête à être installée pour tous : oui / non, et pourquoi.
