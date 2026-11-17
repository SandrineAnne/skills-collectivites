/* Brique commune « traçabilité » — version 1.0.0
   À copier telle quelle dans src/briques/ ; une évolution se propose à la cellule opérationnelle, qui met la brique à jour pour tous.
   Ajoute à tout document produit (rapport, export, impression) la mention :
   « Produit avec <outil> v<version> le <date> à partir de : <fichiers sources (empreinte)> »
   pour savoir, des mois plus tard, avec quoi un document a été fait. Aucun appel réseau. */
(function (racine) {
  'use strict';

  // Empreinte courte (8 caractères) d'un fichier ou d'un texte, calculée dans le navigateur.
  async function empreinte(contenu) {
    const donnees = typeof contenu === 'string' ? new TextEncoder().encode(contenu) : new Uint8Array(await contenu.arrayBuffer());
    const condense = await crypto.subtle.digest('SHA-256', donnees);
    return Array.from(new Uint8Array(condense)).map(o => o.toString(16).padStart(2, '0')).join('').slice(0, 8);
  }

  // sources : [{nom: 'trame-2026.xlsx', empreinte: '1a2b3c4d'}, …] ; date : facultative (aujourd'hui par défaut)
  function produitAvec(outil, version, sources, date) {
    const jour = (date || new Date()).toLocaleDateString('fr-FR');
    const liste = (sources || []).map(s => (s.empreinte ? s.nom + ' (' + s.empreinte + ')' : s.nom)).join(', ');
    return 'Produit avec ' + outil + ' v' + version + ' le ' + jour + ' à partir de : ' + (liste || 'saisie manuelle');
  }

  const brique = { produitAvec, empreinte, VERSION: '1.0.0' };
  racine.Tracabilite = brique;
  if (typeof module !== 'undefined' && module.exports) module.exports = brique;
})(typeof window !== 'undefined' ? window : globalThis);
