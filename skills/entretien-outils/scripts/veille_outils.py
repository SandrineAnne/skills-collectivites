"""Revue de tous les outils d'un dossier : ce qui est à traiter maintenant, à planifier, ou en ordre.

Usage : python3 veille_outils.py <dossier contenant les outils> [--chercher MOT] [--controler] [--date AAAA-MM-JJ]
                                [--sortie revue.md]

Un outil = un sous-dossier (jusqu'à deux niveaux) qui contient README.md et VERSION. Pour chacun, lit son dossier :
docs/composants.md (fin de support), docs/incidents.md (incidents ouverts), docs/derogations.md (revue dépassée),
docs/fiche-dsi.md (essai de restauration, format B), README (référent).
  --chercher MOT  liste les outils dont les composants, dépendances ou images mentionnent MOT (après une faille annoncée)
  --controler     lance aussi le build/fabriquer.py de chaque outil (contrôle complet, sans paquet)
Code de sortie : 1 s'il y a au moins un outil à traiter maintenant, 0 sinon (utile en tâche programmée), 2 si aucun outil trouvé.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import os
import pathlib
import re
import subprocess
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

RE_MARQUEUR = re.compile(r'À[ _-]?COMPLÉTER')
FICHIERS_DEPENDANCES = ('docs/composants.md', 'requirements.txt', 'package.json', 'deploy/compose.yaml', 'deploy/Dockerfile', 'Dockerfile')


@dataclasses.dataclass
class Etat:
    """Ce que la revue a trouvé pour un outil."""
    chemin: pathlib.Path
    nom: str
    version: str
    format: str
    maintenant: list[str] = dataclasses.field(default_factory=list)
    planifier: list[str] = dataclasses.field(default_factory=list)
    rustine: bool = False
    classe: int | None = None


def lire(chemin: pathlib.Path) -> str:
    try:
        return chemin.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ''


def lignes_tableau(texte: str) -> list[list[str]]:
    lignes = [[c.strip() for c in ligne.strip().strip('|').split('|')] for ligne in texte.splitlines()
              if ligne.strip().startswith('|') and not re.match(r'^\|[\s:|-]+\|?$', ligne.strip())]
    return lignes[1:]


def lire_date(valeur: str) -> datetime.date | None:
    # première date trouvée dans le champ : « 01/10/2026, réussi » ou « le 2026-10-01 par la cellule » sont lus aussi
    m = re.search(r'(?<!\d)(\d{2})/(\d{2})/(\d{4})(?!\d)', valeur)
    if m:
        valeur = f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    m = re.search(r'(?<!\d)(\d{4})-(\d{2})(?:-(\d{2}))?(?!\d)', valeur)
    if not m or not 1 <= int(m.group(2)) <= 12:
        return None
    annee, mois = int(m.group(1)), int(m.group(2))
    if m.group(3):
        with contextlib.suppress(ValueError):
            return datetime.date(annee, mois, int(m.group(3)))
        return None
    return datetime.date(annee + (mois == 12), mois % 12 + 1, 1) - datetime.timedelta(days=1)


def trouver_outils(racine: pathlib.Path) -> list[pathlib.Path]:
    candidats = [racine, *[p for p in racine.iterdir() if p.is_dir()]]
    candidats += [q for p in racine.iterdir() if p.is_dir() for q in p.iterdir() if q.is_dir()]
    return sorted({p for p in candidats if (p / 'README.md').exists() and (p / 'VERSION').exists()})


def examiner_composants(etat: Etat, aujourdhui: datetime.date) -> None:
    lignes = [c for c in lignes_tableau(lire(etat.chemin / 'docs' / 'composants.md')) if len(c) >= 4 and c[0]]
    if not lignes or all(RE_MARQUEUR.search(' '.join(c)) for c in lignes):
        etat.planifier.append('composants non listés : on ne saura pas si une faille le touche')
        return
    for cases in lignes:
        date = lire_date(cases[3])
        if date is None and not re.search(r'(?i)sans date|maintenu', cases[3]):
            etat.planifier.append(f'{cases[0]} : date de fin de support inconnue')
        elif date and date < aujourdhui:
            etat.maintenant.append(f'{cases[0]} {cases[1]} : support terminé depuis le {date.isoformat()}')
        elif date and date < aujourdhui + datetime.timedelta(days=183):
            etat.planifier.append(f'{cases[0]} {cases[1]} : fin de support le {date.isoformat()}')


def examiner_suivi(etat: Etat, aujourdhui: datetime.date) -> None:
    for cases in lignes_tableau(lire(etat.chemin / 'docs' / 'incidents.md')):
        if cases and cases[-1].lower().startswith('ouvert'):
            etat.maintenant.append(f'incident ouvert du {cases[0]} : {cases[2] if len(cases) > 2 else "?"}')
    for cases in lignes_tableau(lire(etat.chemin / 'docs' / 'derogations.md')):
        date = lire_date(cases[5]) if len(cases) >= 6 else None
        if cases and cases[0] and not RE_MARQUEUR.search(' '.join(cases)) and date and date < aujourdhui:
            etat.planifier.append(f'exception « {cases[0]} » : revue dépassée ({date.isoformat()})')
    readme = lire(etat.chemin / 'README.md')
    referent = re.search(r'(?im)^\s*-\s*Référent[^:\n]*:\s*(.*)$', readme)
    if not referent or not referent.group(1).strip() or RE_MARQUEUR.search(referent.group(1)):
        etat.planifier.append('référent non indiqué dans le README')


def examiner_restauration(etat: Etat, aujourdhui: datetime.date) -> None:
    if etat.format != 'B':
        return
    ligne = re.search(r'(?im)^\s*-\s*Dernier essai de restauration[^:\n]*:[ \t]*(.*)$', lire(etat.chemin / 'docs' / 'fiche-dsi.md'))
    date = lire_date(ligne.group(1)) if ligne else None
    if date is None:
        etat.planifier.append('aucun essai de restauration daté')
    elif date < aujourdhui - datetime.timedelta(days=365):
        etat.planifier.append(f'dernier essai de restauration il y a plus d\'un an ({date.isoformat()})')


def examiner_editeur(etat: Etat, aujourdhui: datetime.date) -> None:
    """Rustine à réexaminer, questions-tests d'IA à rejouer."""
    rustine = lire(etat.chemin / 'docs' / 'rustine.md')
    if rustine:
        etat.rustine = True
        ligne = re.search(r'(?im)^\s*-\s*Revue avant le[^:\n]*:[ \t]*(.*)$', rustine)
        date = lire_date(ligne.group(1)) if ligne else None
        if date and date < aujourdhui:
            etat.planifier.append(f'rustine à réexaminer (revue prévue le {date.isoformat()}) : le problème de fond est-il réglé ?')
    questions = lire(etat.chemin / 'tests' / 'ia' / 'questions.md')
    if questions:
        dates = [d for d in (lire_date(c[3]) for c in lignes_tableau(questions) if len(c) >= 4) if d]
        if not dates or max(dates) < aujourdhui - datetime.timedelta(days=365):
            etat.planifier.append('questions-tests de la fonction d\'IA à rejouer (plus d\'un an, ou jamais)')


ICI = pathlib.Path(__file__).resolve().parent
RE_VERSION_CONTROLE = re.compile(r"(?m)^VERSION_CONTROLE\s*=\s*'([\d.]+)'")


def version_controle_de_reference(option: str | None) -> str | None:
    """Version du contrôle livrée avec la skill de fabrication, si on la trouve (option --fabrique, ou dossier voisin)."""
    candidats = [pathlib.Path(option)] if option else [
        pathlib.Path(os.environ.get('FABRIQUE_OUTILS', '/nonexistent')), ICI.parent.parent / 'fabrique-outils',
        pathlib.Path('/mnt/skills/plugins/fabrique-outils'), pathlib.Path('/mnt/skills/user/fabrique-outils')]
    for candidat in candidats:
        m = RE_VERSION_CONTROLE.search(lire(candidat / 'scripts' / 'fabriquer.py'))
        if m:
            return m.group(1)
    return None


def en_nombres(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split('.') if x.isdigit())


def examiner_classe(etat: Etat, readme: str, reference: str | None) -> None:
    """Classe de l'outil (1 essentiel, 2 important, 3 confort) et exigences de la classe 1 ; contrôle embarqué ancien."""
    m = re.search(r'(?im)^Classe\s*:\s*([123])\b', readme)
    etat.classe = int(m.group(1)) if m else None
    if etat.classe is None:
        etat.planifier.append('classe non fixée (1 essentiel, 2 important, 3 confort) : à décider avec la cellule')
    if etat.classe == 1:
        if re.search(r'(?im)^Niveau\s*:\s*partag', readme):
            etat.maintenant.append('outil essentiel (classe 1) resté au niveau partagé : le passer au niveau durable')
        if not (etat.chemin / 'docs' / 'mode-degrade.md').exists():
            etat.planifier.append('classe 1 : mode dégradé à écrire (que font les agents si l\'outil est arrêté une journée)')
        if re.search(r'(?im)^\s*-\s*Suppléant[^:\n]*:\s*(?:À COMPLÉTER.*)?$', readme):
            etat.planifier.append('classe 1 : suppléant à désigner')
    embarque = RE_VERSION_CONTROLE.search(lire(etat.chemin / 'build' / 'fabriquer.py'))
    if reference and (embarque is None or en_nombres(embarque.group(1)) < en_nombres(reference)):
        etat.planifier.append(f'contrôle embarqué ancien ({embarque.group(1) if embarque else "sans version"}, référence {reference}) : '
                              'remettre_a_niveau.py --mettre-a-jour-fabriquer')


def controler(etat: Etat, aujourdhui: datetime.date) -> None:
    script = etat.chemin / 'build' / 'fabriquer.py'
    if not script.exists():
        etat.planifier.append('pas de build/fabriquer.py : contrôle impossible (parcours 2, remise à niveau)')
        return
    try:
        res = subprocess.run([sys.executable, str(script), str(etat.chemin), '--sans-paquet', '--date', aujourdhui.isoformat()],
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900, check=False)
    except subprocess.TimeoutExpired:
        etat.planifier.append('contrôle trop long (plus de 15 minutes)')
        return
    if res.returncode != 0:
        nombre = re.search(r'RÉSULTAT : (\d+) point', res.stdout)
        etat.maintenant.append(f'contrôle en échec ({nombre.group(1) if nombre else "?"} point(s)) : voir dist/dossier-transmission.md de l\'outil')


def examiner(chemin: pathlib.Path, aujourdhui: datetime.date, avec_controle: bool, reference: str | None = None) -> Etat:
    readme = lire(chemin / 'README.md')
    titre = re.search(r'(?m)^#\s*(.+)$', readme)
    fmt = re.search(r'(?im)^Format\s*:\s*([ABCD])', readme)
    etat = Etat(chemin, titre.group(1).strip() if titre else chemin.name, lire(chemin / 'VERSION').strip() or '?',
                fmt.group(1).upper() if fmt else '?')
    examiner_composants(etat, aujourdhui)
    examiner_suivi(etat, aujourdhui)
    examiner_restauration(etat, aujourdhui)
    examiner_editeur(etat, aujourdhui)
    examiner_classe(etat, readme, reference)
    if avec_controle:
        controler(etat, aujourdhui)
    return etat


def chercher(outils: list[pathlib.Path], mot: str) -> list[str]:
    trouves = []
    for chemin in outils:
        for relatif in FICHIERS_DEPENDANCES:
            lignes = [ligne.strip() for ligne in lire(chemin / relatif).splitlines() if mot.lower() in ligne.lower()]
            if lignes:
                trouves.append(f'{chemin.name} — {relatif} : {lignes[0][:160]}')
    return trouves


def rediger(racine: pathlib.Path, etats: list[Etat], aujourdhui: datetime.date, recherche: tuple[str, list[str]] | None) -> str:
    def bloc(etat: Etat, elements: list[str]) -> list[str]:
        return [f'### {etat.nom} (v{etat.version}, format {etat.format}) — `{etat.chemin.relative_to(racine) if etat.chemin != racine else "."}`',
                *[f'- {e}' for e in elements], '']
    maintenant = [e for e in etats if e.maintenant]
    planifier = [e for e in etats if not e.maintenant and e.planifier]
    ordre = [e for e in etats if not e.maintenant and not e.planifier]
    lignes = [f'# Revue des outils — {aujourdhui.isoformat()}', '',
              f'{len(etats)} outil(s) examiné(s) : {len(maintenant)} à traiter maintenant, {len(planifier)} à planifier, {len(ordre)} en ordre ; '
              f'dont {sum(e.rustine for e in etats)} rustine(s).', '']
    if recherche:
        mot, trouves = recherche
        lignes += [f'## Outils qui mentionnent « {mot} »', *([f'- {t}' for t in trouves] or ['- aucun']), '']
    lignes += ['## À traiter maintenant', '']
    for etat in maintenant:
        lignes += bloc(etat, etat.maintenant + [f'(à planifier aussi) {p}' for p in etat.planifier])
    lignes += ['- rien', ''] if not maintenant else []
    lignes += ['## À planifier', '']
    for etat in planifier:
        lignes += bloc(etat, etat.planifier)
    lignes += ['- rien', ''] if not planifier else []
    lignes += ['## En ordre', *([f'- {e.nom} (v{e.version}{", classe " + str(e.classe) if e.classe else ""})' for e in ordre] or ['- aucun']), '',
               '## Décision pour chaque outil (journée annuelle)', '', 'Garder · mutualiser · retirer · remonter au processus. Pour une rustine : le problème de fond est-il réglé ?', '',
               'Rappel : la revue lit les dossiers des outils ; un composant absent de docs/composants.md n\'est pas surveillé.']
    return '\n'.join(lignes) + '\n'


def main(argv: list[str]) -> int:
    analyseur = argparse.ArgumentParser(prog='veille_outils.py', description='Revue de tous les outils d\'un dossier.')
    analyseur.add_argument('dossier', help='dossier qui contient les outils (un sous-dossier par outil)')
    analyseur.add_argument('--chercher', metavar='MOT', help='outils qui mentionnent ce composant (après une faille annoncée)')
    analyseur.add_argument('--controler', action='store_true', help='lance aussi le contrôle complet de chaque outil')
    analyseur.add_argument('--date', type=datetime.date.fromisoformat, default=None, metavar='AAAA-MM-JJ')
    analyseur.add_argument('--sortie', help='fichier Markdown du rapport (sinon : affiché)')
    analyseur.add_argument('--fabrique', help='chemin de la skill fabrique-outils (pour repérer les contrôles embarqués anciens)')
    options = analyseur.parse_args(argv)
    racine = pathlib.Path(options.dossier).resolve()
    if not racine.is_dir():
        sys.exit(f'Arrêt : dossier introuvable : {racine}')
    aujourdhui = options.date or datetime.date.today()
    outils = trouver_outils(racine)
    if not outils:
        print(f'Aucun outil avec un dossier (README.md et VERSION) dans {racine}. Pour un outil sans dossier : remettre_a_niveau.py.',
              file=sys.stderr)
        return 2
    reference = version_controle_de_reference(options.fabrique)
    etats = [examiner(chemin, aujourdhui, options.controler, reference) for chemin in outils]
    recherche = (options.chercher, chercher(outils, options.chercher)) if options.chercher else None
    rapport = rediger(racine, etats, aujourdhui, recherche)
    if options.sortie:
        pathlib.Path(options.sortie).write_text(rapport, encoding='utf-8')
        print(f'Rapport écrit : {options.sortie}')
    else:
        print(rapport)
    return 1 if any(e.maintenant for e in etats) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
