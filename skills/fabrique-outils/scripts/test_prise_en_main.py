"""Test navigateur de la prise en main intégrée (module prise-en-main.js de fabrique-outils).

Usage : python3 test_prise_en_main.py <page.html | URL> [--reseau-autorise hote1,hote2]
      (nécessite playwright + chromium : pip install playwright && playwright install chromium)

Vérifie, sur grand écran (1440 px) puis sur téléphone (390 px) :
  - chaque cible data-tuto des étapes existe dans la page ;
  - la fenêtre d'accueil s'ouvre seule à la première ouverture, plus après « visite faite » ;
  - la visite complète : bulle toujours entière à l'écran et sans recouvrir la zone éclairée ;
  - Échap ferme la visite, le bouton « ? Prise en main » la relance ;
  - chaque chapitre du guide s'ouvre ;
  - rien du tutoriel n'apparaît à l'impression de l'outil ;
  - l'encadré « Nouveautés » apparaît après une mise à jour (si l'application en déclare) ;
  - aucune requête vers l'extérieur (hors hôtes déclarés avec --reseau-autorise) ;
  - aucune erreur JavaScript.
Code de sortie 0 si tout est bon, 1 sinon.
"""
from __future__ import annotations

import argparse
import contextlib
import pathlib
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
LARGEUR_MENU_GUIDE = 760
BULLE = """(()=>{const t=document.getElementById('pem-trou').getBoundingClientRect(), b=document.getElementById('pem-bulle').getBoundingClientRect();
  const vide=t.width<2||t.height<2;
  return {titre:document.getElementById('pem-titre-etape').textContent,
          recouvre:!vide && !(b.right<=t.left||b.left>=t.right||b.bottom<=t.top||b.top>=t.bottom),
          entiere:b.left>=0&&b.top>=0&&b.right<=innerWidth&&b.bottom<=innerHeight}})()"""


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
            self.page.reload()
            self.attendre(900)
            self.verifier(not self.page.is_visible('#pem-nouveautes'), 'nouveautés affichées une seule fois')

    def derouler(self) -> list[str]:
        for etape in (self.ouverture, self.visite, self.relance, self.guide, self.impression, self.nouveautes):
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
