"""Test navigateur de la prise en main intégrée (module prise-en-main.js de fabrique-outils).

Usage : python3 test_prise_en_main.py <page.html | URL> [--reseau-autorise hote1,hote2]
      (nécessite playwright + chromium : pip install playwright && playwright install chromium)

Vérifie, sur grand écran (1440 px) puis sur téléphone (390 px) :
  - chaque cible data-tuto des étapes existe dans la page ;
  - la fenêtre d'accueil s'ouvre seule à la première ouverture, plus après « visite faite » ;
  - la visite complète : bulle toujours entière à l'écran et sans recouvrir la zone éclairée ;
  - Échap ferme la visite, le bouton « ? Prise en main » la relance ;
  - chaque chapitre du guide s'ouvre ;
  - le contour de focus clavier garde au moins 3 contre 1 avec son fond, en thème clair et en thème sombre ;
  - à la fermeture d'une fenêtre (accueil, nouveautés) ou de la visite, le focus revient au bouton qui l'a ouverte
    (au bouton « ? Prise en main » quand la fenêtre s'est ouverte seule) ;
  - au clavier, Tab reste dans la bulle de la visite, Échap la ferme ;
  - sur un écran minuscule (320 × 256, un écran de 1280 × 1024 zoomé à 400 %) avec un texte d'étape très long,
    la bulle reste entière à l'écran, son texte défile et le bouton « Suivant » reste cliquable ;
  - rien du tutoriel n'apparaît à l'impression de l'outil ;
  - l'encadré « Nouveautés » apparaît après une mise à jour (si l'application en déclare) ;
  - aucune requête vers l'extérieur (hors hôtes déclarés avec --reseau-autorise) ;
  - aucune erreur JavaScript.
Code de sortie 0 si tout est bon, 1 sinon.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Arrêt : Playwright n'est pas installé. Installer avec : pip install playwright && playwright install chromium")

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

ECRANS = ((1440, 900), (390, 780))
MINI_ECRAN = (320, 256)                           # 1280 × 1024 zoomé à 400 %
CONTRASTE_MINI = 3.0                              # WCAG 1.4.11 / RGAA 10.7 : indicateur de focus
TEXTE_LONG = ''.join('<p>Ce texte d’étape est volontairement très long pour vérifier qu’il défile dans la bulle sans la faire sortir de l’écran. '
                     'Une deuxième phrase prolonge encore le propos. Une troisième phrase ferme le paragraphe.</p>' for _ in range(4))
# Avant le chargement de la page : allonge le texte de chaque étape de la configuration passée à PriseEnMain.init
ALLONGER_ETAPES = '''(texte => { let module;
  Object.defineProperty(window, 'PriseEnMain', { configurable: true, get: () => module, set: m => {
    const init = m.init; m.init = config => { config.etapes.forEach(e => { e.texte = texte; }); return init(config); }; module = m; } });
})(%s)'''
LARGEUR_MENU_GUIDE = 760
# donne le focus à l'élément puis relève la couleur de son contour et la couleur du fond derrière lui
MESURE_FOCUS = """(sel)=>{const e=document.querySelector(sel); if(!e) return null; e.focus(); const cs=getComputedStyle(e);
  let f=e.parentElement, fond=null;
  while(f){const c=getComputedStyle(f).backgroundColor, m=c.match(/[\\d.]+/g); if(m&&(m.length<4||+m[3]>0)){fond=c;break} f=f.parentElement}
  return {couleur:cs.outlineColor, style:cs.outlineStyle, fond:fond||'rgb(255, 255, 255)'}}"""
ATTRIBUTS_BULLE = """(()=>{const b=document.getElementById('pem-bulle'), t=document.getElementById(b.getAttribute('aria-labelledby')||'');
  return {role:b.getAttribute('role'), modal:b.getAttribute('aria-modal'), titre:!!t&&t.textContent.trim().length>0}})()"""
FOCUS_DANS_BULLE = "document.getElementById('pem-bulle').contains(document.activeElement)"
HAUT_BULLE = "Math.round(document.getElementById('pem-bulle').getBoundingClientRect().top)"
TEXTE_QUI_DEFILE = "(()=>{const t=document.querySelector('#pem-bulle .pem-texte'); return t.scrollHeight>t.clientHeight})()"
ACTIF = "(()=>{const a=document.activeElement; return a.getAttribute('data-tuto')||a.id||a.tagName})()"
BULLE = """(()=>{const t=document.getElementById('pem-trou').getBoundingClientRect(), b=document.getElementById('pem-bulle').getBoundingClientRect();
  const vide=t.width<2||t.height<2;
  return {titre:document.getElementById('pem-titre-etape').textContent,
          recouvre:!vide && !(b.right<=t.left||b.left>=t.right||b.bottom<=t.top||b.top>=t.bottom),
          entiere:b.left>=0&&b.top>=0&&b.right<=innerWidth&&b.bottom<=innerHeight}})()"""


def luminance(couleur: str) -> float:
    """Luminance relative WCAG d'une couleur « rgb(r, g, b) » ou « rgba(r, g, b, a) »."""
    composantes = []
    for brut in re.findall(r'[\d.]+', couleur)[:3]:
        c = float(brut) / 255
        composantes.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * composantes[0] + 0.7152 * composantes[1] + 0.0722 * composantes[2]


def contraste(a: str, b: str) -> float:
    clair, sombre = sorted((luminance(a), luminance(b)), reverse=True)
    return (clair + 0.05) / (sombre + 0.05)


class Essai:
    """Un passage complet du tutoriel sur une taille d'écran."""

    def __init__(self, navigateur, url: str, autorises: set[str], largeur: int, hauteur: int):
        self.url, self.largeur = url, largeur
        self.echecs: list[str] = []
        self.sortantes: list[str] = []
        self.erreurs: list[str] = []
        hote_page = urlparse(url).hostname if url.startswith('http') else None
        self.contexte = navigateur.new_context(viewport={'width': largeur, 'height': hauteur})

        def filtre(route) -> None:                    # toute requête vers l'extérieur est bloquée et signalée
            adresse = urlparse(route.request.url)
            if adresse.scheme in ('http', 'https') and adresse.hostname not in autorises and adresse.hostname != hote_page:
                self.sortantes.append(route.request.url)
                route.abort()
            else:
                route.continue_()

        self.contexte.route('**/*', filtre)
        self.page = self.contexte.new_page()
        self.page.on('pageerror', lambda erreur: self.erreurs.append(str(erreur)))

    def verifier(self, condition: bool, libelle: str) -> None:
        print(('  ✓ ' if condition else '  ✗ ') + libelle)
        if not condition:
            self.echecs.append(libelle)

    def attendre(self, millisecondes: int) -> None:
        self.page.wait_for_timeout(millisecondes)

    def ouverture(self) -> None:
        self.page.goto(self.url)
        self.attendre(900)
        manquantes = self.page.evaluate('PriseEnMain.verifierCibles()')
        self.verifier(not manquantes, 'cibles des étapes présentes' + (f' (manquantes : {manquantes})' if manquantes else ''))
        self.verifier(self.page.is_visible('#pem-accueil'), 'accueil ouvert à la première ouverture')

    def visite(self) -> None:
        self.page.click('#pem-go-visite')
        self.attendre(400)
        prevues = self.page.evaluate('PriseEnMain.etat().etapes')
        vues, a_revoir = 0, []
        for _ in range(prevues + 2):                  # marge : des étapes masquées peuvent être sautées
            if not self.page.is_visible('#pem-visite'):
                break
            self.attendre(350)
            bulle = self.page.evaluate(BULLE)
            vues += 1
            if bulle['recouvre'] or not bulle['entiere']:
                a_revoir.append(bulle['titre'])
            self.page.click('#pem-suiv')
        self.attendre(300)
        self.verifier(vues >= 1 and not self.page.is_visible('#pem-visite'), f'visite parcourue jusqu’au bout ({vues} étape(s) affichée(s) sur {prevues})')
        self.verifier(not a_revoir, 'bulle entière et sans recouvrement' + (f' (à revoir : {a_revoir})' if a_revoir else ''))

    def relance(self) -> None:
        self.page.reload()
        self.attendre(900)
        self.verifier(not self.page.is_visible('#pem-accueil'), 'accueil non reproposé une fois la visite faite')
        self.page.click('[data-tuto="aide"]')
        self.attendre(200)
        self.verifier(self.page.is_visible('#pem-accueil'), 'le bouton « ? Prise en main » rouvre l’aide')
        self.page.click('#pem-go-visite')
        self.attendre(300)
        self.page.keyboard.press('ArrowRight')
        self.attendre(300)
        self.page.keyboard.press('Escape')
        self.attendre(200)
        self.verifier(not self.page.is_visible('#pem-visite'), 'flèche puis Échap : la visite se ferme')

    def guide(self) -> None:
        chapitres = self.page.evaluate("PriseEnMain.ouvrirGuide(0), document.querySelectorAll('#pem-guide .pem-ch').length")
        tous_visibles = True
        for i in range(chapitres):
            if self.largeur > LARGEUR_MENU_GUIDE:
                self.page.click(f'#pem-guide nav [data-ch="{i}"]')
            else:
                self.page.evaluate(f"document.querySelector('#pem-guide [data-go=\"{i}\"]') && document.querySelector('#pem-guide [data-go=\"{i}\"]').click()")
            tous_visibles = self.page.is_visible(f'#pem-guide section[data-ch="{i}"]') and tous_visibles
        self.verifier(chapitres >= 2 and tous_visibles, f'guide : {chapitres} chapitres consultables (dont « À propos »)')
        self.page.keyboard.press('Escape')
        self.attendre(150)

    def impression(self) -> None:
        self.page.emulate_media(media='print')
        self.verifier(not self.page.is_visible('[data-tuto="aide"]') and not self.page.is_visible('#pem-guide'), 'tutoriel absent de l’impression de l’outil')
        self.page.emulate_media(media='screen')

    def nouveautes(self) -> None:
        self.page.evaluate("Object.keys(localStorage).filter(k=>k.endsWith('-pem-version')).forEach(k=>localStorage.setItem(k,'0.9.0'))")
        self.page.reload()
        self.attendre(900)
        affiche = self.page.is_visible('#pem-nouveautes')
        print('  · encadré « Nouveautés » après mise à jour :', 'affiché' if affiche else 'non affiché (aucune nouveauté déclarée pour cette version ?)')
        if affiche:
            self.page.click('#pem-ok')
            self.attendre(150)
            actif = self.page.evaluate(ACTIF)
            self.verifier(actif == 'aide', f'nouveautés ouvertes seules, fermées par « J’ai compris » : le focus va au bouton d’aide (focus sur : {actif})')
            self.page.reload()
            self.attendre(900)
            self.verifier(not self.page.is_visible('#pem-nouveautes'), 'nouveautés affichées une seule fois')

    def contour_focus(self) -> None:
        """Le contour de focus (bouton d'aide, fenêtre d'accueil, menu du guide) garde au moins 3 contre 1 avec son fond, dans les deux thèmes."""
        for theme in ('light', 'dark'):
            nom = 'clair' if theme == 'light' else 'sombre'
            self.page.emulate_media(color_scheme=theme)
            mesures = {}
            self.page.keyboard.press('Shift')         # le contour n'apparaît qu'au clavier (:focus-visible)
            mesures['bouton « ? Prise en main »'] = self.page.evaluate(MESURE_FOCUS, '[data-tuto="aide"]')
            self.page.click('[data-tuto="aide"]')
            self.attendre(200)
            self.page.keyboard.press('Shift')
            mesures['boutons de la fenêtre d’accueil'] = self.page.evaluate(MESURE_FOCUS, '#pem-go-visite')
            self.page.keyboard.press('Escape')
            self.page.evaluate('PriseEnMain.ouvrirGuide(0)')
            if self.largeur > LARGEUR_MENU_GUIDE:
                self.page.keyboard.press('Shift')
                mesures['menu du guide (fond grisé)'] = self.page.evaluate(MESURE_FOCUS, '#pem-guide nav [data-ch="0"]')
            self.page.keyboard.press('Escape')
            self.attendre(150)
            for quoi, m in mesures.items():
                rapport = contraste(m['couleur'], m['fond']) if m and m['style'] != 'none' else 0.0
                self.verifier(rapport >= CONTRASTE_MINI,
                              f'contour de focus lisible (≥ {CONTRASTE_MINI:g} contre 1) en thème {nom} : {quoi} ({rapport:.2f} contre 1)')
        self.page.emulate_media(color_scheme='light')

    def retour_du_focus(self) -> None:
        """À la fermeture, le focus revient au contrôle qui a ouvert la fenêtre, ou au bouton d'aide quand elle s'est ouverte seule."""
        self.page.reload()
        self.attendre(900)
        for fermeture, libelle in (('#pem-plus-tard', 'clic sur « Fermer »'), ('Escape', 'Échap')):
            self.page.click('[data-tuto="aide"]')
            self.attendre(200)
            if fermeture == 'Escape':
                self.page.keyboard.press('Escape')
            else:
                self.page.click(fermeture)
            self.attendre(150)
            actif = self.page.evaluate(ACTIF)
            self.verifier(actif == 'aide', f'accueil ouvert depuis le bouton d’aide, fermé par {libelle} : le focus revient au bouton (focus sur : {actif})')
        for fermeture, libelle in (('Escape', 'Échap'), ('#pem-plus-tard', 'clic sur « Plus tard »'), ('#pem-jamais', 'clic sur « Ne plus proposer »')):
            self.page.evaluate('localStorage.clear()')
            self.page.reload()
            self.attendre(900)
            if fermeture == 'Escape':
                self.page.keyboard.press('Escape')
            else:
                self.page.click(fermeture)
            self.attendre(150)
            actif = self.page.evaluate(ACTIF)
            self.verifier(actif == 'aide', f'accueil ouvert seul au premier lancement, fermé par {libelle} : le focus va au bouton d’aide (focus sur : {actif})')

    def clavier_visite(self) -> None:
        """Au clavier : dialogue étiqueté, Tab reste dans la bulle (dans les deux sens), Échap ferme et rend le focus au bouton d'aide."""
        self.page.click('[data-tuto="aide"]')
        self.page.click('#pem-go-visite')
        self.attendre(400)
        attributs = self.page.evaluate(ATTRIBUTS_BULLE)
        self.verifier(attributs == {'role': 'dialog', 'modal': 'true', 'titre': True}, f'bulle de la visite : dialogue modal avec un titre ({attributs})')
        for touche in ('Tab', 'Shift+Tab'):
            dedans = []
            for _ in range(6):
                self.page.keyboard.press(touche)
                dedans.append(self.page.evaluate(FOCUS_DANS_BULLE))
            self.verifier(all(dedans), f'visite : {touche} garde le focus dans la bulle')
        self.page.keyboard.press('Escape')
        self.attendre(200)
        actif = self.page.evaluate(ACTIF)
        self.verifier(not self.page.is_visible('#pem-visite') and actif == 'aide', f'visite : Échap la ferme et le focus revient au bouton d’aide (focus sur : {actif})')

    def petit_ecran(self) -> None:
        """320 × 256 avec un texte d'étape très long : bulle entière à l'écran, texte qui défile, « Suivant » cliquable."""
        largeur, hauteur = MINI_ECRAN
        page = self.contexte.new_page()
        page.on('pageerror', lambda erreur: self.erreurs.append(str(erreur)))
        page.set_viewport_size({'width': largeur, 'height': hauteur})
        page.add_init_script(ALLONGER_ETAPES % json.dumps(TEXTE_LONG, ensure_ascii=False))
        page.goto(self.url)
        page.wait_for_timeout(900)
        page.click('[data-tuto="aide"]')
        page.click('#pem-go-visite')
        page.wait_for_timeout(400)
        prevues = page.evaluate('PriseEnMain.etat().etapes')
        debordent, bloquees, defile, tab_dehors = [], [], [], []
        for _ in range(prevues + 2):
            if not page.is_visible('#pem-visite'):
                break
            page.wait_for_timeout(350)
            bulle = page.evaluate(BULLE)
            if not bulle['entiere']:
                debordent.append(f"{bulle['titre']} (haut {page.evaluate(HAUT_BULLE)} px)")
            defile.append(page.evaluate(TEXTE_QUI_DEFILE))
            page.keyboard.press('Tab')
            tab_dehors.append(not page.evaluate(FOCUS_DANS_BULLE))
            try:
                page.click('#pem-suiv', timeout=3000)
            except Exception:                         # bouton masqué, recouvert ou hors de l'écran
                bloquees.append(bulle['titre'])
                break
        page.wait_for_timeout(300)
        self.verifier(not debordent, f'écran {largeur} × {hauteur}, texte long : bulle entière dans l’écran' + (f' (à revoir : {debordent})' if debordent else ''))
        self.verifier(bool(defile) and all(defile), f'écran {largeur} × {hauteur}, texte long : le texte défile dans la bulle')
        self.verifier(not bloquees and not page.is_visible('#pem-visite'),
                      f'écran {largeur} × {hauteur}, texte long : « Suivant » reste cliquable jusqu’à la fin de la visite' + (f' (bloqué à : {bloquees})' if bloquees else ''))
        self.verifier(not any(tab_dehors), f'écran {largeur} × {hauteur}, texte long : Tab garde le focus dans la bulle')
        page.close()

    def derouler(self) -> list[str]:
        for etape in (self.ouverture, self.visite, self.relance, self.guide, self.impression, self.contour_focus,
                      self.retour_du_focus, self.clavier_visite, self.nouveautes, self.petit_ecran):
            etape()
        tentees = f' (tentées : {sorted(set(self.sortantes))[:5]})' if self.sortantes else ''
        self.verifier(not self.sortantes, 'aucune requête vers l’extérieur' + tentees)
        self.verifier(not self.erreurs, 'aucune erreur JavaScript' + (f' : {self.erreurs}' if self.erreurs else ''))
        self.contexte.close()
        return self.echecs


def lire_options(argv: list[str]) -> tuple[str, set[str]]:
    analyseur = argparse.ArgumentParser(prog='test_prise_en_main.py', description='Test navigateur du tutoriel de prise en main.')
    analyseur.add_argument('cible', help='page.html ou URL')
    analyseur.add_argument('--reseau-autorise', default='', metavar='HOTES', help='hôtes externes autorisés, séparés par des virgules')
    options = analyseur.parse_args(argv)
    est_url = options.cible.startswith(('http://', 'https://'))
    if not est_url and not pathlib.Path(options.cible).exists():
        sys.exit(f'Arrêt : fichier introuvable : {options.cible}')
    url = options.cible if est_url else pathlib.Path(options.cible).resolve().as_uri()
    return url, {hote.strip() for hote in options.reseau_autorise.split(',') if hote.strip()}


def main(argv: list[str]) -> int:
    url, autorises = lire_options(argv)
    echecs: list[str] = []
    with sync_playwright() as playwright:
        navigateur = playwright.chromium.launch()
        for largeur, hauteur in ECRANS:
            print(f'\n— Écran {largeur} × {hauteur}')
            echecs += Essai(navigateur, url, autorises, largeur, hauteur).derouler()
        navigateur.close()
    print('\nRÉSULTAT :', 'tout est bon' if not echecs else f'{len(echecs)} point(s) à corriger')
    return 0 if not echecs else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
