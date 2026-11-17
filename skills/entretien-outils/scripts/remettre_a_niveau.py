"""Ajoute à la copie d'un outil existant le dossier qui lui manque, à partir des gabarits de la fabrique, sans rien écraser.

Usage : python3 remettre_a_niveau.py <copie_de_l_outil> --copie --format A|B|C|D [--niveau partage|durable]
                                     [--titre "Nom affiché"] [--version 1.0.0] [--fabrique CHEMIN] [--mettre-a-jour-fabriquer]

  --copie     obligatoire : confirme que l'on travaille sur une copie, jamais sur l'original en service
  --version   version à documenter si l'outil n'a pas de fichier VERSION (par défaut 1.0.0 : l'outil est déjà en service)
  --fabrique  chemin de la skill fabrique-outils (par défaut : cherchée à côté de cette skill)

Règles : un fichier présent est conservé tel quel ; un README existant reçoit seulement les lignes « Version »,
« Format » et « Niveau » qui lui manquent, en tête ; .gitignore reçoit « .env » s'il manque ; si le code n'est pas
dans src/, il est déclaré dans build/controles.json au lieu d'être déplacé. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import filecmp
import importlib.util
import json
import os
import pathlib
import re
import shutil
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

ICI = pathlib.Path(__file__).resolve().parent
EXT_CODE = {'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.vue', '.ps1', '.sh'}
HORS_CODE = {'docs', 'tests', 'build', 'deploy', 'dist', 'data', 'node_modules', '.git', '__pycache__', '.venv', 'venv'}
NOTE_SPEC = ('> SPEC reconstituée à partir de l\'outil existant : chaque règle déduite du code porte la mention '
             '« déduite du code, à confirmer par le métier ». Statut « brouillon » jusqu\'à cette confirmation.\n\n')
AIDE_TESTS = ('Tests de caractérisation : ce que l\'outil fait aujourd\'hui, sur des exemples inventés, avec le résultat actuel\n'
              'comme résultat attendu (même discutable : le marquer « comportement actuel, à confirmer par le métier »).\n'
              'Fonctions « test_… » dans des fichiers test_*.py (ou *.test.js) : build/fabriquer.py les exécute.\n')


def trouver_fabrique(option: str | None) -> pathlib.Path:
    candidats = [pathlib.Path(option)] if option else [
        pathlib.Path(os.environ.get('FABRIQUE_OUTILS', '/nonexistent')), ICI.parent.parent / 'fabrique-outils',
        pathlib.Path('/mnt/skills/plugins/fabrique-outils'), pathlib.Path('/mnt/skills/user/fabrique-outils')]
    for candidat in candidats:
        if (candidat / 'scripts' / 'creer_projet.py').exists() and (candidat / 'assets' / 'gabarits').is_dir():
            return candidat.resolve()
    sys.exit('Arrêt : skill fabrique-outils introuvable. Indiquer son chemin avec --fabrique.')


def charger_creer_projet(fabrique: pathlib.Path):
    """Réutilise les gabarits et la sélection de la fabrique : une seule source pour la structure d'un dossier."""
    spec = importlib.util.spec_from_file_location('creer_projet_fabrique', fabrique / 'scripts' / 'creer_projet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nom_court(dossier: pathlib.Path) -> str:
    nom = re.sub(r'[^a-z0-9-]+', '-', dossier.name.lower()).strip('-')
    return nom[:41] or 'outil'


class Remise:
    """Ce qui est créé, complété ou conservé ; rien n'est jamais écrasé."""

    def __init__(self, racine: pathlib.Path, valeurs: dict[str, str]):
        self.racine, self.valeurs = racine, valeurs
        self.crees: list[str] = []
        self.completes: list[str] = []
        self.conserves: list[str] = []
        self.remarques: list[str] = []

    def creer(self, relatif: str, texte: str) -> None:
        cible = self.racine / relatif
        if cible.exists():
            self.conserves.append(relatif)
            return
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding='utf-8')
        self.crees.append(relatif)

    def completer_readme(self) -> None:
        chemin = self.racine / 'README.md'
        texte = chemin.read_text(encoding='utf-8')
        attendues = (('Version', self.valeurs['VERSION']), ('Format', self.valeurs['FORMAT']), ('Niveau', self.valeurs['NIVEAU']))
        manquantes = [f'{cle} : {valeur}' for cle, valeur in attendues if not re.search(rf'(?im)^{cle}\s*:', texte)]
        if not manquantes:
            self.conserves.append('README.md')
            return
        bloc = '\n'.join(manquantes) + '\n'
        titre = re.search(r'(?m)^#\s.*\n', texte)
        neuf = texte[:titre.end()] + '\n' + bloc + texte[titre.end():] if titre else f'# {self.valeurs["TITRE"]}\n\n{bloc}\n{texte}'
        chemin.write_text(neuf, encoding='utf-8')
        self.completes.append('README.md (lignes ajoutées en tête : ' + ', '.join(m.split(' :')[0] for m in manquantes) + ')')

    def completer_changelog(self) -> None:
        """Crée le CHANGELOG, ou ajoute en tête d'un CHANGELOG existant l'entrée de la version documentée."""
        v, date = self.valeurs['VERSION'], self.valeurs['DATE']
        entree = (f'## [{v}] — {date}\n### Ajouté\n'
                  '- Dossier de l\'outil reconstitué (outil déjà en service, version documentée pour la première fois).\n\n')
        chemin = self.racine / 'CHANGELOG.md'
        if not chemin.exists():
            self.creer('CHANGELOG.md', f'# Journal des versions — {self.valeurs["TITRE"]}\n\n{entree}')
            return
        texte = chemin.read_text(encoding='utf-8')
        if re.search(r'(?m)^##\s*\[?\d+\.\d+\.\d+', texte):
            self.conserves.append('CHANGELOG.md')
            return
        titre = re.search(r'(?m)^#\s.*\n', texte)
        neuf = texte[:titre.end()] + '\n' + entree + texte[titre.end():] if titre else entree + texte
        chemin.write_text(neuf, encoding='utf-8')
        self.completes.append(f'CHANGELOG.md (entrée {v} ajoutée en tête, historique conservé)')

    def completer_gitignore(self, gabarit: str) -> None:
        chemin = self.racine / '.gitignore'
        if not chemin.exists():
            self.creer('.gitignore', gabarit)
            return
        texte = chemin.read_text(encoding='utf-8')
        if re.search(r'(?m)^\.env\s*$', texte):
            self.conserves.append('.gitignore')
            return
        chemin.write_text(texte.rstrip('\n') + '\n# Ajouté lors de la remise à niveau : jamais de secret dans le dépôt\n.env\n*.env\n!.env.exemple\n',
                          encoding='utf-8')
        self.completes.append('.gitignore (exclusion de .env ajoutée)')


def poser_gabarits(remise: Remise, creer_projet) -> None:
    valeurs, racine = remise.valeurs, remise.racine
    for gabarit in sorted(creer_projet.GABARITS.rglob('*')):
        relatif = gabarit.relative_to(creer_projet.GABARITS)
        if not gabarit.is_file() or not creer_projet.gabarit_retenu(relatif, valeurs):
            continue
        texte = gabarit.read_text(encoding='utf-8')
        for cle, valeur in valeurs.items():
            texte = texte.replace('{{' + cle + '}}', valeur)
        cible = creer_projet.cible_du_gabarit(relatif, valeurs['NOM'])
        if cible == 'README.md' and (racine / 'README.md').exists():
            remise.completer_readme()
        elif cible == '.gitignore':
            remise.completer_gitignore(texte)
        elif cible == 'CHANGELOG.md':
            remise.completer_changelog()
        else:
            remise.creer(cible, texte)


def poser_spec_et_version(remise: Remise, creer_projet) -> None:
    valeurs = remise.valeurs
    if valeurs['NIVEAU'] == 'partagé':
        spec = creer_projet.SPEC_COURTE.format(titre=valeurs['TITRE'])
    else:
        spec = creer_projet.spec_depuis_modele(valeurs['TITRE'])
    version = valeurs['VERSION']
    spec = re.sub(r'(?m)^(#\s*SPEC.*?\bv)\d+\.\d+', lambda m: m.group(1) + '.'.join(version.split('.')[:2]), spec, count=1)
    remise.creer('SPEC.md', NOTE_SPEC + spec)
    remise.creer('VERSION', version + '\n')
    if not (remise.racine / 'tests').exists():
        remise.creer('tests/LISEZMOI.md', AIDE_TESTS)


def poser_controle(remise: Remise, fabrique: pathlib.Path, mettre_a_jour: bool) -> None:
    source, cible = fabrique / 'scripts' / 'fabriquer.py', remise.racine / 'build' / 'fabriquer.py'
    if not cible.exists():
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, cible)
        remise.crees.append('build/fabriquer.py')
    elif filecmp.cmp(source, cible, shallow=False):
        remise.conserves.append('build/fabriquer.py (déjà à jour)')
    elif mettre_a_jour:
        shutil.copy2(cible, cible.with_name('fabriquer.py.ancien'))
        shutil.copy2(source, cible)
        remise.completes.append('build/fabriquer.py (remplacé par la version de la fabrique ; l\'ancien est gardé en fabriquer.py.ancien)')
    else:
        remise.conserves.append('build/fabriquer.py')
        remise.remarques.append('build/fabriquer.py diffère de celui de la fabrique : relancer avec --mettre-a-jour-fabriquer pour le remplacer')
    declarer_code(remise)


def declarer_code(remise: Remise) -> None:
    """Le code reste où il est : s'il n'est pas dans src/, on le déclare pour que les contrôles le trouvent."""
    racine = remise.racine
    controles = racine / 'build' / 'controles.json'
    if (racine / 'src').exists() or controles.exists():
        return
    racines_code = sorted(p.name for p in racine.iterdir() if p.name not in HORS_CODE and not p.name.startswith('.')
                          and ((p.is_file() and p.suffix.lower() in EXT_CODE)
                               or (p.is_dir() and any(f.suffix.lower() in EXT_CODE for f in p.rglob('*')))))
    if racines_code:
        remise.creer('build/controles.json', json.dumps({'code': racines_code}, ensure_ascii=False, indent=2) + '\n')
        remise.remarques.append(f'Code laissé en place et déclaré dans build/controles.json : {", ".join(racines_code)}')


def lire_options(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(prog='remettre_a_niveau.py', description='Ajoute le dossier manquant à la copie d\'un outil existant.')
    analyseur.add_argument('dossier', help='copie de travail de l\'outil')
    analyseur.add_argument('--copie', action='store_true', help='confirme que l\'on travaille sur une copie (obligatoire)')
    analyseur.add_argument('--format', required=True, type=str.upper, choices=['A', 'B', 'C', 'D'])
    analyseur.add_argument('--niveau', default='durable', choices=['durable', 'partage', 'partagé'])
    analyseur.add_argument('--rustine', action='store_true', help='ajoute la fiche rustine (outil qui contourne un logiciel, une trame ou un processus)')
    analyseur.add_argument('--ia', action='store_true', help='ajoute les questions-tests (outil qui utilise une IA à l\'usage)')
    analyseur.add_argument('--briques', action='store_true', help='copie les briques communes dans src/briques/')
    analyseur.add_argument('--classe', type=int, choices=(1, 2, 3), help='1 essentiel, 2 important, 3 confort (la classe 1 ajoute la page du mode dégradé)')
    analyseur.add_argument('--titre', help='nom affiché de l\'outil')
    analyseur.add_argument('--version', default='1.0.0', help='version à documenter si l\'outil n\'a pas de fichier VERSION')
    analyseur.add_argument('--fabrique', help='chemin de la skill fabrique-outils')
    analyseur.add_argument('--mettre-a-jour-fabriquer', action='store_true', help='remplace un build/fabriquer.py différent (l\'ancien est gardé)')
    analyseur.add_argument('--date', type=datetime.date.fromisoformat, default=None, metavar='AAAA-MM-JJ')
    return analyseur.parse_args(argv)


def afficher(remise: Remise) -> None:
    print(f'Remise à niveau de {remise.racine} (format {remise.valeurs["FORMAT"]}, niveau {remise.valeurs["NIVEAU"]}, '
          f'version documentée {remise.valeurs["VERSION"]})\n')
    for titre, elements in (('Créés', remise.crees), ('Complétés', remise.completes), ('Conservés tels quels', remise.conserves)):
        print(f'{titre} ({len(elements)}) :' + ''.join(f'\n  - {e}' for e in elements))
    for remarque in remise.remarques:
        print(f'! {remarque}')
    print('\nÉtapes suivantes :\n  1. releve_outil.py (si ce n\'est pas fait), puis remplir README, SPEC reconstituée et docs/composants.md'
          '\n  2. Écrire les tests de caractérisation dans tests/\n  3. python3 build/fabriquer.py --brouillon, puis traiter dans l\'ordre de reprise-sans-dossier.md')


def main(argv: list[str]) -> int:
    options = lire_options(argv)
    racine = pathlib.Path(options.dossier).resolve()
    if not racine.is_dir():
        sys.exit(f'Arrêt : dossier introuvable : {racine}')
    if not options.copie:
        sys.exit('Arrêt : confirmer avec --copie que vous travaillez sur une copie de l\'outil, jamais sur l\'original en service.')
    partage = options.niveau.startswith('partag')
    if partage and options.format != 'A':
        sys.exit('Arrêt : le niveau partagé ne convient qu\'au format A. Un outil sur serveur, sur poste ou dans Grist est durable.')
    version = (racine / 'VERSION').read_text(encoding='utf-8').strip() if (racine / 'VERSION').exists() else options.version
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        sys.exit(f'Arrêt : version « {version} » invalide (attendu x.y.z).')
    fabrique = trouver_fabrique(options.fabrique)
    creer_projet = charger_creer_projet(fabrique)
    nom = nom_court(racine)
    valeurs = {'NOM': nom, 'TITRE': options.titre or racine.name, 'VERSION': version, 'FORMAT': options.format,
               'NIVEAU': 'partagé' if partage else 'durable', 'DATE': (options.date or datetime.date.today()).isoformat(),
               'PORT': '8150', 'PORT_INTERNE': '80', 'IMAGE': 'À-COMPLÉTER:0.0.0', 'DOMAINE': f'{nom}.exemple.fr',
               'OU_TROUVER': f'https://{nom}.exemple.fr' if options.format == 'B' else 'À COMPLÉTER'}
    remise = Remise(racine, valeurs)
    poser_gabarits(remise, creer_projet)
    poser_spec_et_version(remise, creer_projet)
    remise.crees += creer_projet.poser_options(racine, valeurs, options.rustine, options.ia, options.briques, options.classe)
    poser_controle(remise, fabrique, options.mettre_a_jour_fabriquer)
    afficher(remise)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
