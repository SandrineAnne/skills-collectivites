"""Intègre le module de prise en main dans un fichier HTML autonome (format A).

Usage : python3 integrer_prise_en_main.py page.html sortie.html
Remplace <link rel="stylesheet" href="…prise-en-main.css"> et <script src="…prise-en-main.js"></script>
par leur contenu : le fichier de sortie fonctionne seul, sans aucun fichier à côté ni appel réseau.
Chaque balise doit être présente une seule fois ; sinon le script s'arrête avec un message clair.
La page d'origine n'est jamais modifiée.
"""
from __future__ import annotations

import contextlib
import pathlib
import re
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

BALISES = ((r'<link[^>]+href="[^"]*prise-en-main\.css"[^>]*>', 'prise-en-main.css', 'style'),
           (r'<script[^>]+src="[^"]*prise-en-main\.js"[^>]*></script>', 'prise-en-main.js', 'script'))


def integrer(html: str, page: pathlib.Path, motif: str, fichier: str, balise: str) -> str:
    """Remplace la balise qui appelle le fichier par son contenu."""
    trouves = re.findall(motif, html)
    if len(trouves) != 1:
        sys.exit(f'Arrêt : balise {fichier} trouvée {len(trouves)} fois dans {page.name} (attendu : 1).')
    nom = re.search(r'(?:href|src)="([^"]+)"', trouves[0]).group(1)
    chemin = page.parent / nom
    if not chemin.exists():
        sys.exit(f'Arrêt : {nom} introuvable à côté de {page.name} (cherché : {chemin}).')
    contenu = chemin.read_text(encoding='utf-8')
    if '</' + balise in contenu.lower():
        sys.exit(f'Arrêt : {fichier} contient « </{balise} », incompatible avec une intégration directe.')
    return html.replace(trouves[0], f'<{balise} data-module="prise-en-main">\n{contenu}\n</{balise}>')


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.exit('Usage : python3 integrer_prise_en_main.py page.html sortie.html')
    page, sortie = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    if not page.exists():
        sys.exit(f'Arrêt : fichier introuvable : {page}')
    if page.resolve() == sortie.resolve():
        sys.exit('Arrêt : la sortie doit être un autre fichier que la page d\'origine (on ne travaille jamais sur l\'original).')
    html = page.read_text(encoding='utf-8')
    for motif, fichier, balise in BALISES:
        html = integrer(html, page, motif, fichier, balise)
    sortie.write_text(html, encoding='utf-8')
    print(f'{sortie.name} : module intégré ({len(html) // 1024} Ko), aucun fichier externe nécessaire.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
