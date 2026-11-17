# Tutoriel de prise en main

Ne pas réécrire de tutoriel : utiliser le module prêt à l'emploi, issu de la « Prise en main » d'un premier outil et rendu indépendant de l'outil qui l'accueille.

```
assets/prise-en-main/prise-en-main.js    le module (aucune dépendance, aucun appel réseau)
assets/prise-en-main/prise-en-main.css   styles : charte graphique, mode sombre, téléphone, impression
assets/prise-en-main/exemple.html        page fictive qui montre l'intégration complète
scripts/integrer_prise_en_main.py        intègre le module dans un fichier HTML unique (format A)
scripts/test_prise_en_main.py            test navigateur (Playwright), grand écran et téléphone
```

## Ce que voit l'utilisateur

1. **À la première ouverture :** une fenêtre d'accueil (à quoi sert l'outil, jusqu'à trois idées clés) avec « Faire la visite guidée », « Lire le guide complet », « Plus tard » et « Ne plus proposer au démarrage ».
2. **La visite :** l'écran s'assombrit, l'élément visé est éclairé, une bulle l'explique en une ou deux phrases. Suivant, Précédent, flèches du clavier, Échap pour quitter.
3. **Le bouton permanent « ? Prise en main »** rouvre l'aide à tout moment.
4. **Le guide complet**, en chapitres, imprimable en A4 portrait ; un dernier chapitre « À propos » est ajouté automatiquement (version, référent et suppléant, confidentialité, lien vers la page du wiki).
5. **Après une mise à jour :** un encadré « Nouveautés de la version x.y », affiché une seule fois.

La mémorisation porte la version majeure : après un changement d'usage (x.0.0), l'accueil se représente.

## Intégrer en quatre gestes

1. Copier `prise-en-main.js` et `prise-en-main.css` dans le projet (`src/prise-en-main/`).
2. Poser un attribut stable `data-tuto="<nom>"` sur chaque élément que la visite doit montrer. Ne jamais viser un élément par sa position ou une classe de mise en forme.
3. Charger les deux fichiers, puis appeler `PriseEnMain.init` (modèle complet dans `exemple.html`) :

```js
PriseEnMain.init({
  appli: 'renommage-dsu',               // identifiant court : clés de mémorisation
  nom: 'Renommage des pièces',          // affiché à l'utilisateur
  version: '1.1.0',                     // lu dans le fichier VERSION par le script de fabrication
  bouton: '#barre',                     // où placer « ? Prise en main » (sinon bouton flottant)
  referent: 'cellule opérationnelle', suppleant: '…', lienDoc: 'https://…',
  signalement: 'https://…',   // formulaire ou catégorie « Outils maison » de l’outil de tickets : ajoute « Signaler un problème » au chapitre « À propos »
  dateVersion: '2026-11-15', peremptionMois: 6, lienDerniereVersion: 'https://…',   // outil local : bandeau « vérifiez qu'il n'existe pas une version plus récente » passé ce délai
  confidentialite: 'Les pièces restent sur le serveur de la collectivité…',
  accueil: { intro: '…', duree: '2 minutes', idees: [{ titre: '…', texte: '…' }] },
  etapes: [                              // 8 à 15 étapes ; sans « cible » : bulle centrée
    { cible: 'depot', titre: 'Déposer un lot', texte: '<p>…</p>' },
    { cible: 'journal', titre: 'Le journal', texte: '<p>…</p>', avant: () => ouvrir('journal') },
  ],
  surFin: () => ouvrir('lot'),           // remise en état après la visite (facultatif)
  guide: [{ titre: 'L’essentiel', intro: '…', html: '…' }],   // essentiel, pas à pas, vocabulaire, FAQ, règles d'or
  nouveautes: { '1.1': '<ul><li>…</li></ul>' },               // clé = version x.y
});
```

4. Format A : `python3 scripts/integrer_prise_en_main.py page.html sortie.html` remplace les deux balises par leur contenu, pour obtenir un fichier unique. Format B : servir les deux fichiers avec l'application. Format C : même intégration si l'interface est une page web locale ; sinon, reproduire le même déroulé avec les moyens de l'interface. Format D (Grist) : un guide dans une page d'accueil du document suffit. **Limite connue :** l'équivalent pour un MSI à interface native ou un document Grist n'est pas encore défini ; le dire à la cellule plutôt que d'improviser.

## Règles

- Une étape dont l'élément n'existe pas dans la page est retirée ; un élément présent mais masqué (onglet fermé) reste, et la fonction `avant` de l'étape l'affiche.
- Textes pour non-experts : phrases courtes, un geste par phrase, noms exacts des boutons de l'écran, apostrophe typographique ’.
- La visite ne modifie aucune donnée et n'apparaît jamais dans les impressions de l'outil.
- Ne pas réutiliser l'identifiant global `PriseEnMain` ni les classes `pem-` dans l'application.
- La configuration est écrite par le développeur, jamais par un utilisateur : le module échappe les textes simples et n'accepte dans `lienDoc` et `signalement` que `http(s)://` ou un chemin relatif ; le champ `confidentialite` et les `texte` / `html` des étapes sont du HTML de confiance (jamais de donnée importée).

## Contrôles avant livraison

- `python3 scripts/test_prise_en_main.py <page.html | URL>` : cibles présentes, accueil à la première ouverture seulement, visite complète sans bulle tronquée ni recouvrement (1440 px et 390 px), Échap, bouton de relance, chapitres du guide, absence à l'impression, nouveautés une seule fois, aucune requête vers l’extérieur (le test bloque et signale toute requête hors des hôtes passés avec `--reseau-autorise`), zéro erreur JavaScript.
- À l'œil : deux ou trois étapes en capture d'écran, le mode sombre, l'impression du guide.
