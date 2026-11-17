/* Brique commune « reconnaître une trame » — version 1.0.0
   À copier telle quelle dans src/briques/ ; une évolution se propose à la cellule opérationnelle.
   Pour un outil qui lit des fichiers produits par d'autres (trame d'une agence, export d'un logiciel) :
   reconnaît la version du format à partir des colonnes, ou dit clairement ce qui manque.
   versions : {'Trame 2026': ['Code station', 'Date du bilan', 'Débit'], 'Trame 2025': [...]} */
(function (racine) {
  'use strict';

  const normaliser = t => String(t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();

  function reconnaitreVersion(colonnes, versions) {
    const presentes = new Set((colonnes || []).map(normaliser));
    let proche = null;
    for (const [nom, attendues] of Object.entries(versions || {})) {
      const manquantes = attendues.filter(c => !presentes.has(normaliser(c)));
      if (manquantes.length === 0) return { version: nom, manquantes: [] };
      if (!proche || manquantes.length < proche.manquantes.length) proche = { version: nom, manquantes };
    }
    const detail = proche ? ' Version la plus proche : ' + proche.version + ' ; il manque : ' + proche.manquantes.join(', ') + '.' : '';
    throw new Error('Format de fichier non reconnu.' + detail +
      ' Si la trame a changé, prévenez le référent de l’outil : il faut ajouter cette nouvelle version.');
  }

  const brique = { reconnaitreVersion, normaliser, VERSION: '1.0.0' };
  racine.Entrees = brique;
  if (typeof module !== 'undefined' && module.exports) module.exports = brique;
})(typeof window !== 'undefined' ? window : globalThis);
