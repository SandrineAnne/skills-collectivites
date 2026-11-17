"""Passe un outil à sa version suivante, partout à la fois, et ajoute l'entrée du CHANGELOG.

Usage : python3 nouvelle_version.py <dossier_de_l_outil> correction|evolution|majeure "Ce qui change, en mots simples"
                                    [--rubrique Corrigé|Ajouté|Modifié|Retiré|Sécurité] [--date AAAA-MM-JJ] [--simulation]

  correction  x.y.Z : un défaut corrigé (rubrique par défaut : Corrigé)
  evolution   x.Y.0 : une évolution compatible (rubrique par défaut : Ajouté)
  majeure     X.0.0 : un changement d'usage ou de données (rubrique par défaut : Modifié)

Met à jour : VERSION ; les lignes « Version : » et « Version documentée : » du README, de docs/ et de deploy/ ;
les constantes APP_VERSION ; le champ version de package.json ; les mentions de version des fichiers deploy/*.yaml ;
le numéro de la SPEC (évolution et majeure) ; une nouvelle entrée en tête du CHANGELOG.
Ne remplace que l'ancien numéro exact : une autre version écrite ailleurs est signalée, jamais modifiée.
--simulation montre ce qui changerait, sans rien écrire. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import pathlib
import re
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

RUBRIQUES = {'correction': 'Corrigé', 'evolution': 'Ajouté', 'majeure': 'Modifié'}
EXT_CODE = {'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.json', '.yaml', '.yml', '.vue'}
IGNORES = {'.git', 'node_modules', 'dist', '__pycache__', 'data', '.venv', 'venv', 'vendor', 'build'}


def suivante(version: str, nature: str) -> str:
    majeur, mineur, correctif = (int(x) for x in version.split('.'))
    if nature == 'majeure':
        return f'{majeur + 1}.0.0'
    if nature == 'evolution':
        return f'{majeur}.{mineur + 1}.0'
    return f'{majeur}.{mineur}.{correctif + 1}'


def fichiers(racine: pathlib.Path, extensions: set[str]) -> list[pathlib.Path]:
    return [p for p in sorted(racine.rglob('*'))
            if p.is_file() and p.suffix.lower() in extensions and not any(part in IGNORES for part in p.relative_to(racine).parts)]


class Modifications:
    """Les remplacements à faire, fichier par fichier ; rien n'est écrit avant la fin des contrôles."""

    def __init__(self, racine: pathlib.Path, ancienne: str, nouvelle: str):
        self.racine, self.ancienne, self.nouvelle = racine, ancienne, nouvelle
        self.textes: dict[pathlib.Path, str] = {}
        self.ecarts: list[str] = []

    def texte(self, chemin: pathlib.Path) -> str:
        if chemin not in self.textes:
            self.textes[chemin] = chemin.read_text(encoding='utf-8')
        return self.textes[chemin]

    def remplacer(self, chemin: pathlib.Path, motif: str, gabarit: str, decrire: str) -> int:
        """Remplace l'ancienne version là où le motif la désigne ; signale les autres numéros trouvés au même endroit."""
        avant = self.texte(chemin)
        trouves = list(re.finditer(motif, avant, re.M))
        for m in trouves:
            if m.group('v') != self.ancienne:
                self.ecarts.append(f'{chemin.relative_to(self.racine)} : {decrire} = {m.group("v")} (attendu {self.ancienne}), non modifié')
        apres = re.sub(motif, lambda m: gabarit.format(debut=m.group('debut'), fin=m.group('fin') if 'fin' in m.groupdict() else '',
                                                        v=self.nouvelle) if m.group('v') == self.ancienne else m.group(0), avant, flags=re.M)
        self.textes[chemin] = apres
        return sum(1 for m in trouves if m.group('v') == self.ancienne)

    def changes(self) -> list[pathlib.Path]:
        return [p for p, t in self.textes.items() if not p.exists() or p.read_text(encoding='utf-8') != t]


RE_LIGNE_VERSION = r'^(?P<debut>.*\bVersion(?: documentée)?\s*:\s*\**\s*)(?P<v>\d+\.\d+\.\d+)'
RE_APP_VERSION = r'(?P<debut>APP_VERSION\s*[:=]\s*[\'"])(?P<v>\d+\.\d+\.\d+)(?P<fin>[\'"])'
RE_PACKAGE = r'(?P<debut>"version"\s*:\s*")(?P<v>\d+\.\d+\.\d+)(?P<fin>")'
RE_YAML_VERSION = r'^(?P<debut>\s*(?:app_version|version_attendue|outil\.version)\s*:\s*["\']?)(?P<v>\d+\.\d+\.\d+)(?P<fin>["\']?)'


def preparer(racine: pathlib.Path, ancienne: str, nouvelle: str, nature: str) -> Modifications:
    mods = Modifications(racine, ancienne, nouvelle)
    documents = [racine / 'README.md', *sorted((racine / 'docs').glob('*.md')), *sorted((racine / 'deploy').glob('*.md'))]
    for doc in documents:
        if doc.exists() and mods.remplacer(doc, RE_LIGNE_VERSION, '{debut}{v}', 'ligne « Version »') == 0 \
                and not re.search(RE_LIGNE_VERSION, mods.texte(doc), re.M):
            mods.ecarts.append(f'{doc.relative_to(racine)} : aucune ligne « Version : » (à ajouter à la main)')
    for code in fichiers(racine, EXT_CODE):
        if 'APP_VERSION' in mods.texte(code):
            mods.remplacer(code, RE_APP_VERSION, '{debut}{v}{fin}', 'APP_VERSION')
        if code.name == 'package.json':
            mods.remplacer(code, RE_PACKAGE, '{debut}{v}{fin}', 'version de package.json')
        if code.parent.name == 'deploy' and code.suffix in ('.yaml', '.yml'):
            mods.remplacer(code, RE_YAML_VERSION, '{debut}{v}{fin}', 'version du déploiement')
    spec = racine / 'SPEC.md'
    if spec.exists() and nature != 'correction':
        mods.textes[spec] = re.sub(r'^(#\s*SPEC.*?\bv)\d+\.\d+', lambda m: m.group(1) + '.'.join(nouvelle.split('.')[:2]),
                                   mods.texte(spec), count=1, flags=re.M)
    mods.textes[racine / 'VERSION'] = nouvelle + '\n'
    return mods


def entree_changelog(mods: Modifications, rubrique: str, resume: str, date: str) -> None:
    chemin = mods.racine / 'CHANGELOG.md'
    texte = mods.texte(chemin) if chemin.exists() else '# Journal des versions\n\n'
    entree = f'## [{mods.nouvelle}] — {date}\n### {rubrique}\n- {resume}\n\n'
    position = re.search(r'(?m)^##\s', texte)
    mods.textes[chemin] = texte[:position.start()] + entree + texte[position.start():] if position else texte.rstrip('\n') + '\n\n' + entree


def lire_options(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(prog='nouvelle_version.py', description='Passe un outil à sa version suivante, partout à la fois.')
    analyseur.add_argument('dossier', help='dossier de l\'outil (celui qui contient VERSION)')
    analyseur.add_argument('nature', choices=['correction', 'evolution', 'majeure'])
    analyseur.add_argument('resume', help='ce qui change pour les utilisateurs, en mots simples')
    analyseur.add_argument('--rubrique', choices=['Corrigé', 'Ajouté', 'Modifié', 'Retiré', 'Sécurité'], help='rubrique du CHANGELOG')
    analyseur.add_argument('--date', type=datetime.date.fromisoformat, default=None, metavar='AAAA-MM-JJ')
    analyseur.add_argument('--simulation', action='store_true', help='montre ce qui changerait, sans rien écrire')
    return analyseur.parse_args(argv)


def main(argv: list[str]) -> int:
    options = lire_options(argv)
    racine = pathlib.Path(options.dossier).resolve()
    fichier_version = racine / 'VERSION'
    if not fichier_version.exists():
        sys.exit(f'Arrêt : {racine} n\'a pas de fichier VERSION. Pour un outil sans dossier, utiliser d\'abord remettre_a_niveau.py.')
    ancienne = fichier_version.read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', ancienne):
        sys.exit(f'Arrêt : VERSION contient « {ancienne} » au lieu de x.y.z. Rien n\'a été modifié.')
    if not options.resume.strip():
        sys.exit('Arrêt : le résumé du changement est vide.')
    nouvelle = suivante(ancienne, options.nature)
    mods = preparer(racine, ancienne, nouvelle, options.nature)
    date = (options.date or datetime.date.today()).isoformat()
    entree_changelog(mods, options.rubrique or RUBRIQUES[options.nature], options.resume.strip(), date)
    changes = mods.changes()
    print(f'{racine.name} : {ancienne} → {nouvelle} ({options.nature})' + (' — SIMULATION, rien n\'est écrit' if options.simulation else ''))
    for chemin in changes:
        print(f'  {"modifierait" if options.simulation else "modifié"} : {chemin.relative_to(racine)}')
    for ecart in mods.ecarts:
        print(f'  ! {ecart}')
    if not options.simulation:
        for chemin in changes:
            chemin.write_text(mods.textes[chemin], encoding='utf-8')
        print('\nÉtape suivante : python3 build/fabriquer.py (il vérifie que la version est identique partout et que les tests passent).')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
