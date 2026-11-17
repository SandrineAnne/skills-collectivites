"""Compare la grille intégrée (references/grille-vigilance.md) à celle de la cybersécurité.

Usage : python3 verifier_grille.py <SKILL.md ou fichier .skill de la cybersécurité>

Compare : les points (numéro, texte, barème), le score maximal et les seuils vert / orange / rouge.
Code de sortie 0 si identique, 1 sinon (avec la liste des écarts) : à lancer avant chaque livraison de la skill
et chaque fois que la cybersécurité publie une nouvelle version de sa grille.
"""
from __future__ import annotations

import contextlib
import pathlib
import re
import sys
import zipfile

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

GRILLE_INTEGREE = pathlib.Path(__file__).resolve().parent.parent / 'references' / 'grille-vigilance.md'


def lire(chemin: str | pathlib.Path) -> str:
    """Texte d'un fichier Markdown, ou du SKILL.md contenu dans un fichier .skill."""
    fichier = pathlib.Path(chemin)
    if fichier.suffix != '.skill':
        return fichier.read_text(encoding='utf-8')
    with zipfile.ZipFile(fichier) as archive:
        noms = [nom for nom in archive.namelist() if nom.endswith('SKILL.md')]
        if len(noms) != 1:
            sys.exit(f'Arrêt : {len(noms)} SKILL.md dans {fichier.name} (attendu : 1).')
        return archive.read(noms[0]).decode('utf-8')


def points(texte: str) -> dict[int, tuple[str, str]]:
    """Numéro du point → (libellé, barème)."""
    return {int(m.group(1)): (re.sub(r'\s+', ' ', m.group(2)).strip(), m.group(3).strip())
            for m in re.finditer(r'^\| (\d+) \|[^|]*\| ([^|]+) \| ([^|]+) \|$', texte, re.M)}


def seuils(texte: str) -> dict[str, list]:
    separateur = r'\*\*\s*{}\s*:?\s*\*\*\s*:?\s*'      # tolère « **Vert** : » comme « **Vert :** »
    return {'maximum': re.findall(r'Score maximal : (\d+)', texte),
            'vert': re.findall(separateur.format('Vert') + r'(\d+) à (\d+)', texte),
            'orange': re.findall(separateur.format('Orange') + r'(\d+) à (\d+)', texte),
            'rouge': re.findall(separateur.format('Rouge') + r'(\d+) points', texte)}


def comparer(integree: str, reference: str) -> list[str]:
    points_a, points_b, seuils_a, seuils_b = points(integree), points(reference), seuils(integree), seuils(reference)
    ecarts = []
    if not points_b:
        ecarts.append('aucun point reconnu dans la grille de référence (tableau « | n° | thème | point | barème | ») : format modifié ?')
    for numero in sorted(set(points_a) | set(points_b)):
        if points_a.get(numero) != points_b.get(numero):
            ecarts.append(f'point {numero} : intégrée = {points_a.get(numero)} · cybersécurité = {points_b.get(numero)}')
    ecarts += [f'{cle} : intégrée = {seuils_a[cle]} · cybersécurité = {seuils_b[cle]}' for cle in seuils_a if seuils_a[cle] != seuils_b[cle]]
    if not ecarts and not all(seuils_b.values()):
        ecarts.append('score maximal ou seuils introuvables dans la grille de référence : format modifié ?')
    return ecarts


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.exit('Usage : python3 verifier_grille.py <SKILL.md ou fichier .skill de la cybersécurité>')
    if not pathlib.Path(argv[0]).exists():
        sys.exit(f'Arrêt : fichier introuvable : {argv[0]}')
    reference = lire(argv[0])
    ecarts = comparer(lire(GRILLE_INTEGREE), reference)
    if ecarts:
        print('ÉCART avec la grille de la cybersécurité :')
        for ecart in ecarts:
            print('  - ' + ecart)
        return 1
    valeurs = seuils(reference)
    print(f'identique : {len(points(reference))} points, score maximal {valeurs["maximum"][0]}, seuils '
          f'{valeurs["vert"][0][0]}-{valeurs["vert"][0][1]} / {valeurs["orange"][0][0]}-{valeurs["orange"][0][1]} / {valeurs["rouge"][0]}+')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
