/* ==========================================================================
   PRISE EN MAIN INTÉGRÉE — module générique (skill fabrique-outils)
   Version du module : 1.0.0
   Origine : la visite guidée d'un premier outil, rendue indépendante
   de l'outil qui l'accueille.

   Ce que fait le module :
   1. fenêtre d'accueil à la première ouverture (par version majeure de l'appli) ;
   2. visite guidée sur l'écran réel : zone éclairée, bulle, clavier ← → Échap ;
   3. guide complet en chapitres, imprimable en A4 portrait ;
   4. encadré « Nouveautés de la version x.y » une fois après une mise à jour ;
   5. bouton permanent « ? Prise en main ».

   Aucune dépendance, aucun appel réseau, aucune donnée de l'outil modifiée.
   L'application fournit ses textes et ses étapes : PriseEnMain.init({...}).
   Les éléments visés portent un attribut stable data-tuto="<nom>".
   ========================================================================== */
(function (global) {
  'use strict';

  const MODULE = '1.2.0';
  let C = null;                                   // configuration fournie par l'application
  const T = { i: 0, etapes: [], couche: null, raf: 0, retour: null };

  /* ---------- petits outils ---------- */
  const lsGet = k => { try { return global.localStorage.getItem(k); } catch (e) { return null; } };
  const lsSet = (k, v) => { try { global.localStorage.setItem(k, String(v)); } catch (e) { /* navigation privée */ } };
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const attendre = ms => new Promise(r => setTimeout(r, ms));
  // Durcissement : la configuration vient du développeur, jamais d'un utilisateur ; on échappe tout de même les textes simples
  // et on n'accepte dans un lien que http(s) ou un chemin relatif (jamais « javascript: »).
  const esc = t => String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const urlSure = u => /^(https?:\/\/|\/|\.{0,2}\/|#)/i.test(String(u || '')) ? esc(u) : '';
  const majeure = v => String(v || '1').split('.')[0];
  const mineure = v => { const p = String(v || '1.0').split('.'); return p[0] + '.' + (p[1] || '0'); };
  const cleVu = () => C.appli + '-pem-v' + majeure(C.version);
  const cleVersion = () => C.appli + '-pem-version';
  /* « import » vise [data-tuto="import"] ; un sélecteur CSS (#, ., [) est accepté tel quel */
  const selecteur = c => (/^[#.\[]/.test(c) ? c : '[data-tuto="' + c + '"]');
  function visible(c) {
    for (const e of document.querySelectorAll(selecteur(c))) {
      const r = e.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return e;
    }
    return null;
  }
  const FOCUSABLES = 'button:not([disabled]),a[href],input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])';
  function pieger(e, boite) {                      // garde le focus clavier dans la fenêtre ouverte
    if (e.key !== 'Tab' || !boite) return;
    const f = [...boite.querySelectorAll(FOCUSABLES)].filter(x => x.offsetParent !== null);
    if (!f.length) return;
    const premier = f[0], dernier = f[f.length - 1];
    if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus(); }
    else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus(); }
  }
  function fermerTout() { fermerVisite(true); fermerFenetre('pem-accueil'); fermerFenetre('pem-nouveautes'); fermerGuide(); }

  /* ---------- fenêtres simples (accueil, nouveautés) ---------- */
  /* Contrôle où rendre le focus à la fermeture d'une fenêtre : celui qui l'a ouverte (s'il reste dans la page),
     sinon le bouton permanent « ? Prise en main » (ouverture automatique au premier lancement). */
  function ouvreur() {
    const a = document.activeElement;
    if (a && a !== document.body && a !== document.documentElement && a.isConnected && !a.closest('.pem-couche, #pem-guide')) return a;
    return document.querySelector('[data-tuto="aide"]');
  }
  function ouvrirFenetre(id, html, focusSel) {
    const retour = ouvreur();
    fermerTout();
    const L = el('div', 'pem-couche'); L.id = id; L._retour = retour;
    L.appendChild(el('div', 'pem-voile'));
    const b = el('div', 'pem-fenetre', html);
    b.setAttribute('role', 'dialog'); b.setAttribute('aria-modal', 'true'); b.setAttribute('aria-labelledby', id + '-titre');
    L.appendChild(b); document.body.appendChild(L);
    L.addEventListener('keydown', e => { pieger(e, b); });
    const f = b.querySelector(focusSel); if (f) f.focus();
    return b;
  }
  function fermerFenetre(id, rendreFocus) {
    const L = document.getElementById(id); if (!L) return;
    L.remove(); document.removeEventListener('keydown', L._echap || (() => {}));
    if (rendreFocus) {   // l'ouvreur a pu quitter la page entre-temps : on se rabat sur le bouton d'aide
      const cible = L._retour && L._retour.isConnected ? L._retour : document.querySelector('[data-tuto="aide"]');
      if (cible) cible.focus({ preventScroll: true });
    }
  }
  function surEchap(id, fn) {
    const L = document.getElementById(id);
    L._echap = e => { if (e.key === 'Escape') { e.stopPropagation(); fn(); } };
    document.addEventListener('keydown', L._echap);
  }

  /* ---------- 1. accueil ---------- */
  function ouvrirAccueil(auto) {
    const a = C.accueil || {};
    const idees = (a.idees || []).slice(0, 3).map((x, k) =>
      '<div class="pem-idee"><span class="pem-n">' + (k + 1) + '</span><b>' + x.titre + '</b>' + x.texte + '</div>').join('');
    const b = ouvrirFenetre('pem-accueil',
      '<h2 id="pem-accueil-titre">Bienvenue dans ' + C.nom + '</h2>' +
      (a.intro ? '<p class="pem-intro">' + a.intro + '</p>' : '') +
      (idees ? '<div class="pem-idees">' + idees + '</div>' : '') +
      '<div class="pem-actions">' +
        '<button type="button" class="pem-b pri" id="pem-go-visite">Faire la visite guidée' + (a.duree ? ' (' + a.duree + ')' : '') + '</button>' +
        '<button type="button" class="pem-b" id="pem-go-guide">Lire le guide complet</button>' +
        '<button type="button" class="pem-b lien" id="pem-plus-tard">' + (auto ? 'Plus tard' : 'Fermer') + '</button>' +
      '</div>' +
      '<p class="pem-pied">Cette aide reste disponible à tout moment avec le bouton <b>? Prise en main</b>.' +
      (auto ? ' <button type="button" class="pem-b lien" id="pem-jamais">Ne plus proposer au démarrage</button>' : '') + '</p>',
      '#pem-go-visite');
    const vu = () => { lsSet(cleVu(), '1'); lsSet(cleVersion(), C.version); };
    const fermer = () => fermerFenetre('pem-accueil', true);
    surEchap('pem-accueil', fermer);
    b.querySelector('#pem-go-visite').addEventListener('click', () => { vu(); fermerFenetre('pem-accueil'); lancerVisite(); });
    b.querySelector('#pem-go-guide').addEventListener('click', () => { vu(); fermerFenetre('pem-accueil'); ouvrirGuide(0); });
    b.querySelector('#pem-plus-tard').addEventListener('click', fermer);
    const j = b.querySelector('#pem-jamais'); if (j) j.addEventListener('click', () => { vu(); fermer(); });
  }

  /* ---------- 2. nouveautés ---------- */
  function ouvrirNouveautes() {
    const html = (C.nouveautes || {})[mineure(C.version)];
    lsSet(cleVersion(), C.version);
    if (!html) return false;
    const b = ouvrirFenetre('pem-nouveautes',
      '<h2 id="pem-nouveautes-titre">Nouveautés de la version ' + mineure(C.version) + '</h2>' + html +
      '<div class="pem-actions"><button type="button" class="pem-b pri" id="pem-ok">J’ai compris</button>' +
      '<button type="button" class="pem-b" id="pem-nv-guide">Ouvrir le guide</button></div>', '#pem-ok');
    const fermer = () => fermerFenetre('pem-nouveautes', true);
    surEchap('pem-nouveautes', fermer);
    b.querySelector('#pem-ok').addEventListener('click', fermer);
    b.querySelector('#pem-nv-guide').addEventListener('click', () => { fermerFenetre('pem-nouveautes'); ouvrirGuide(0); });
    return true;
  }

  /* ---------- 3. visite guidée ---------- */
  function lancerVisite() {
    fermerTout();
    T.retour = document.querySelector('[data-tuto="aide"]');
    /* une étape dont l'élément n'existe pas du tout (fonction absente, profil) est retirée ;
       un élément présent mais masqué reste : la fonction « avant » de l'étape peut l'afficher */
    T.etapes = C.etapes.filter(s => !s.cible || document.querySelector(selecteur(s.cible)));
    T.i = 0;
    const L = el('div', 'pem-couche'); L.id = 'pem-visite';
    L.innerHTML = '<div class="pem-bloc"></div><div class="pem-trou" id="pem-trou"></div>' +
      '<div class="pem-bulle" id="pem-bulle" role="dialog" aria-modal="true" aria-labelledby="pem-titre-etape"></div>';
    document.body.appendChild(L); T.couche = L;
    global.addEventListener('resize', placer); document.addEventListener('scroll', placer, true);
    document.addEventListener('keydown', clavier, true);
    const boucle = () => { if (!T.couche) return; placer(); T.raf = requestAnimationFrame(boucle); }; boucle();
    afficher(1);
  }
  function clavier(e) {
    if (!T.couche) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); fermerVisite(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); aller(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); aller(-1); }
    else pieger(e, document.getElementById('pem-bulle'));
  }
  function aller(sens) {
    const j = T.i + sens;
    if (j < 0) return;
    if (j >= T.etapes.length) return fermerVisite();
    T.i = j; afficher(sens);
  }
  async function afficher(sens) {
    const s = T.etapes[T.i]; if (!s) return fermerVisite();
    if (typeof s.avant === 'function') { try { await s.avant(); } catch (e) { /* l'étape reste lisible */ } await attendre(80); }
    if (!T.couche) return;
    const cible = s.cible ? visible(s.cible) : null;
    if (s.cible && !cible) {                       // toujours masqué : on passe à l'étape suivante
      const j = T.i + (sens || 1);
      if (j < 0 || j >= T.etapes.length) return fermerVisite();
      T.i = j; return afficher(sens);
    }
    const n = T.etapes.length, dernier = T.i === n - 1;
    const bulle = document.getElementById('pem-bulle');
    bulle.innerHTML =
      '<div class="pem-num">Étape ' + (T.i + 1) + ' sur ' + n + '</div>' +
      '<h3 id="pem-titre-etape">' + s.titre + '</h3><div class="pem-texte">' + s.texte + '</div>' +
      '<div class="pem-nav"><span class="pem-points" aria-hidden="true">' +
        T.etapes.map((_, k) => '<i class="' + (k === T.i ? 'on' : '') + '"></i>').join('') + '</span>' +
        (T.i ? '<button type="button" class="pem-b" id="pem-prec">Précédent</button>' : '') +
        '<button type="button" class="pem-b pri" id="pem-suiv">' + (dernier ? 'Terminer' : 'Suivant') + '</button></div>' +
      '<div class="pem-quitter"><button type="button" class="pem-b lien" id="pem-stop">Quitter la visite</button></div>';
    bulle.querySelector('#pem-suiv').addEventListener('click', () => aller(1));
    const p = bulle.querySelector('#pem-prec'); if (p) p.addEventListener('click', () => aller(-1));
    bulle.querySelector('#pem-stop').addEventListener('click', () => fermerVisite());
    if (cible) {
      const r = cible.getBoundingClientRect();
      if (r.top < 60 || r.bottom > innerHeight - 20) { cible.scrollIntoView({ block: 'center' }); await attendre(60); }
    }
    placer();
    bulle.querySelector('#pem-suiv').focus({ preventScroll: true });
  }
  function placer() {
    if (!T.couche) return;
    const s = T.etapes[T.i], trou = document.getElementById('pem-trou'), bulle = document.getElementById('pem-bulle');
    if (!s || !trou || !bulle) return;
    const cible = s.cible ? visible(s.cible) : null;
    const vw = innerWidth, vh = innerHeight, m = 12;
    let r = null;
    if (cible) {
      const q = cible.getBoundingClientRect(), pad = s.marge || 6;
      const L = Math.max(4, q.left - pad), H = Math.max(4, q.top - pad), R = Math.min(vw - 4, q.right + pad), B = Math.min(vh - 4, q.bottom + pad);
      Object.assign(trou.style, { display: 'block', left: L + 'px', top: H + 'px', width: Math.max(0, R - L) + 'px', height: Math.max(0, B - H) + 'px' });
      r = { left: L, top: H, right: R, bottom: B };
    } else {
      Object.assign(trou.style, { display: 'block', left: (vw / 2) + 'px', top: (vh / 2) + 'px', width: '0px', height: '0px' });
    }
    const w = bulle.offsetWidth, h = bulle.offsetHeight;
    let x, y;
    if (!r) { x = (vw - w) / 2; y = (vh - h) / 2; }
    else if (r.bottom + 14 + h < vh - m) { y = r.bottom + 14; x = r.left; }
    else if (r.top - 14 - h > m) { y = r.top - 14 - h; x = r.left; }
    else if (r.left - 14 - w > m) { x = r.left - 14 - w; y = r.top; }
    else if (r.right + 14 + w < vw - m) { x = r.right + 14; y = r.top; }
    else { x = (vw - w) / 2; y = vh - h - m; }
    x = Math.min(Math.max(m, x), vw - w - m); y = Math.min(Math.max(m, y), vh - h - m);
    bulle.style.left = x + 'px'; bulle.style.top = y + 'px';
    /* texte plus haut que la bulle : il défile, et on peut le faire défiler au clavier (zone atteignable par Tab) */
    const texte = bulle.querySelector('.pem-texte');
    if (texte) {
      const defile = texte.scrollHeight > texte.clientHeight + 1;
      if (defile !== texte.hasAttribute('tabindex')) {
        if (defile) { texte.tabIndex = 0; texte.setAttribute('role', 'region'); texte.setAttribute('aria-labelledby', 'pem-titre-etape'); }
        else { texte.removeAttribute('tabindex'); texte.removeAttribute('role'); texte.removeAttribute('aria-labelledby'); }
      }
    }
  }
  function fermerVisite(silencieux) {
    if (!T.couche) return;
    T.couche.remove(); T.couche = null; cancelAnimationFrame(T.raf);
    global.removeEventListener('resize', placer); document.removeEventListener('scroll', placer, true);
    document.removeEventListener('keydown', clavier, true);
    if (typeof C.surFin === 'function') { try { C.surFin(); } catch (e) { /* remise en état facultative */ } }
    if (!silencieux && T.retour) T.retour.focus({ preventScroll: true });
  }

  /* ---------- 4. guide complet ---------- */
  function chapitres() {
    const apropos = ['À propos', 'Version, référent et confidentialité',
      '<p><b>' + esc(C.nom) + '</b>, version ' + esc(C.version) + '.</p>' +
      (C.referent ? '<p>Référent : ' + esc(C.referent) + (C.suppleant ? ' · suppléant : ' + esc(C.suppleant) : '') + '.</p>' : '') +
      (C.confidentialite ? '<div class="pem-encadre">' + C.confidentialite + '</div>' : '') +
      (urlSure(C.lienDoc) ? '<p>Documentation complète : <a href="' + urlSure(C.lienDoc) + '" target="_blank" rel="noopener noreferrer">page de l’outil sur le wiki</a>.</p>' : '') +
      (urlSure(C.signalement) ? '<p>Un problème, une idée ? <a href="' + urlSure(C.signalement) + '" target="_blank" rel="noopener noreferrer">Signaler un problème</a> (le référent est prévenu).</p>' : '')];
    return (C.guide || []).map(c => [c.titre, c.intro || '', c.html || '']).concat([apropos]);
  }
  function construireGuide() {
    if (document.getElementById('pem-guide')) return;
    const CH = chapitres();
    const g = el('div', ''); g.id = 'pem-guide'; g.hidden = true;
    g.innerHTML = '<div class="pem-guide" role="dialog" aria-modal="true" aria-labelledby="pem-guide-titre">' +
      '<div class="pem-guide-tete"><h2 id="pem-guide-titre">Guide de prise en main<span>' + C.nom + ' · version ' + C.version + '</span></h2>' +
        '<button type="button" class="pem-b" id="pem-g-visite">Visite guidée</button>' +
        '<button type="button" class="pem-b" id="pem-g-imprimer">Imprimer le guide</button>' +
        '<button type="button" class="pem-b pri" id="pem-g-fermer">Fermer</button></div>' +
      '<nav class="pem-guide-nav" aria-label="Chapitres">' +
        CH.map((c, i) => '<button type="button" data-ch="' + i + '"><span class="pem-n">' + (i + 1) + '</span><span>' + c[0] + '</span></button>').join('') + '</nav>' +
      '<div class="pem-guide-corps" id="pem-guide-corps">' + CH.map((c, i) =>
        '<section class="pem-ch" data-ch="' + i + '"><h3>' + (i + 1) + '. ' + c[0] + '</h3>' + (c[1] ? '<p class="pem-ch-intro">' + c[1] + '</p>' : '') + c[2] +
        '<div class="pem-pager">' + (i ? '<button type="button" class="pem-b" data-go="' + (i - 1) + '">← ' + CH[i - 1][0] + '</button>' : '<span></span>') +
        (i < CH.length - 1 ? '<button type="button" class="pem-b pri" data-go="' + (i + 1) + '">' + CH[i + 1][0] + ' →</button>' : '<span></span>') +
        '</div></section>').join('') + '</div></div>';
    document.body.appendChild(g);
    g.addEventListener('click', e => { if (e.target === g) fermerGuide(); });
    g.querySelectorAll('nav [data-ch]').forEach(b => b.addEventListener('click', () => chapitre(+b.dataset.ch)));
    g.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => chapitre(+b.dataset.go)));
    g.querySelector('#pem-g-fermer').addEventListener('click', fermerGuide);
    g.querySelector('#pem-g-visite').addEventListener('click', () => { fermerGuide(); lancerVisite(); });
    g.querySelector('#pem-g-imprimer').addEventListener('click', imprimerGuide);
    g.addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); fermerGuide(); } else pieger(e, g.firstChild); });
  }
  function chapitre(i) {
    document.querySelectorAll('#pem-guide .pem-ch').forEach(s => { s.style.display = (+s.dataset.ch === i) ? 'block' : 'none'; });
    document.querySelectorAll('#pem-guide nav button').forEach(b => b.setAttribute('aria-current', +b.dataset.ch === i ? 'true' : 'false'));
    document.getElementById('pem-guide-corps').scrollTop = 0;
  }
  function ouvrirGuide(i) {
    fermerTout(); construireGuide();
    document.getElementById('pem-guide').hidden = false; chapitre(i || 0);
    document.getElementById('pem-g-fermer').focus();
  }
  function fermerGuide() { const g = document.getElementById('pem-guide'); if (g) g.hidden = true; }
  function imprimerGuide() {
    const ds = [...document.querySelectorAll('#pem-guide details')], ouverts = ds.map(d => d.open);
    ds.forEach(d => { d.open = true; });
    document.body.classList.add('pem-impression');
    /* A4 portrait posé le temps de l'impression seulement : les autres impressions de l'outil ne changent pas */
    const st = document.createElement('style'); st.textContent = '@page{size:A4 portrait;margin:14mm 15mm}'; document.head.appendChild(st);
    const fin = () => { document.body.classList.remove('pem-impression'); st.remove(); ds.forEach((d, k) => { d.open = ouverts[k]; }); global.removeEventListener('afterprint', fin); };
    global.addEventListener('afterprint', fin);
    try { global.print(); } catch (e) { /* impression indisponible */ }
    setTimeout(() => { if (!global.matchMedia('print').matches) fin(); }, 1500);
  }

  /* ---------- 5. bouton et démarrage ---------- */
  function creerBouton() {
    if (document.querySelector('[data-tuto="aide"]')) return;
    const b = el('button', 'pem-btn', '<span class="pem-q" aria-hidden="true">?</span>Prise en main');
    b.type = 'button'; b.setAttribute('data-tuto', 'aide');
    b.title = 'Visite guidée et guide complet, pour découvrir l’outil pas à pas';
    const parent = C.bouton ? document.querySelector(C.bouton) : null;
    if (parent) parent.appendChild(b); else { b.classList.add('pem-btn-flottant'); document.body.appendChild(b); }
    b.addEventListener('click', () => ouvrirAccueil(false));
  }
  // Outil local : rien ne le met à jour tout seul. Passé « peremptionMois » (6 par défaut) après « dateVersion »,
  // un bandeau discret invite à vérifier qu'il n'existe pas une version plus récente. Aucun appel réseau.
  function avertirPeremption() {
    const date = new Date(C.dateVersion || '');
    if (isNaN(date) || lsGet(C.appli + '-pem-perime-' + C.version)) return;
    const limite = new Date(date); limite.setMonth(limite.getMonth() + (Number(C.peremptionMois) || 6));
    if (new Date() < limite) return;
    const b = document.createElement('div');
    b.className = 'pem-perime'; b.setAttribute('role', 'status');
    const texte = document.createElement('span');
    texte.textContent = 'Cette version de ' + C.nom + ' date du ' + date.toLocaleDateString('fr-FR') + '. Vérifiez qu’il n’en existe pas une plus récente.';
    b.appendChild(texte);
    const lien = urlSure(C.lienDerniereVersion);
    if (lien) {
      const a = document.createElement('a');
      a.href = C.lienDerniereVersion; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = 'Voir la dernière version';
      b.appendChild(a);
    }
    const fermer = document.createElement('button');
    fermer.type = 'button'; fermer.textContent = 'Compris';
    fermer.addEventListener('click', () => { lsSet(C.appli + '-pem-perime-' + C.version, '1'); b.remove(); });
    b.appendChild(fermer);
    document.body.insertBefore(b, document.body.firstChild);
  }
  function demarrer() {
    creerBouton();
    avertirPeremption();
    if (!lsGet(cleVu())) { setTimeout(() => ouvrirAccueil(true), 300); return; }
    if (lsGet(cleVersion()) !== C.version) setTimeout(ouvrirNouveautes, 300);
  }
  function verifierCibles() {                      // pour les tests : cibles introuvables dans la page
    return C.etapes.filter(s => s.cible && !s.facultatif && !document.querySelector(selecteur(s.cible))).map(s => s.cible);
  }
  function init(config) {
    const manque = ['appli', 'nom', 'version', 'etapes', 'guide'].filter(k => !config || config[k] == null);
    if (manque.length) { console.error('PriseEnMain.init : paramètre(s) manquant(s) : ' + manque.join(', ')); return; }
    C = config;
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', demarrer); else demarrer();
  }

  global.PriseEnMain = {
    init, ouvrirAccueil: () => ouvrirAccueil(false), lancerVisite, ouvrirGuide, verifierCibles,
    etat: () => ({ module: MODULE, etape: T.couche ? T.i : null, etapes: T.etapes.length }),
  };
})(window);
