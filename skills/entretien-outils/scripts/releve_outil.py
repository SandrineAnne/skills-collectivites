"""Relevé d'un outil existant, sans le modifier : ce qu'il contient, ce sur quoi il repose, ce qui manque à son dossier.

Usage : python3 releve_outil.py <dossier ou fichier de l'outil> [--sortie releve.md]

Lit les fichiers et écrit un relevé en Markdown (par défaut : releve-<nom>.md dans le dossier courant) :
format probable, points d'entrée, dépendances (figées ou non), bibliothèques embarquées qui annoncent leur version,
ressources chargées depuis Internet, secrets possibles (valeurs masquées), données de personnes possibles,
versions annoncées, éléments de dossier présents ou manquants, et un tableau de composants prêt à reprendre
dans docs/composants.md. Un relevé lit les fichiers : il se trompe parfois, tout est à vérifier.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import datetime
import json
import pathlib
import re
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

IGNORES = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', '.pytest_cache'}
EXT_TEXTE = {'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.css', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
             '.txt', '.md', '.sh', '.ps1', '.xml', '.csv', '.vue', '.conf', '.env', ''}
EXT_CODE = {'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.vue', '.ps1', '.sh'}
DOSSIER_FABRIQUE = ['README.md', 'SPEC.md', 'CHANGELOG.md', 'VERSION', '.gitignore', 'reseau-autorise.txt', 'tests/',
                    'docs/composants.md', 'docs/exploitation.md', 'docs/fiche-dsi.md', 'docs/partage.md', 'build/fabriquer.py']
CADRICIELS_SERVEUR = re.compile(r'(?im)^\s*(flask|fastapi|django|uvicorn|gunicorn|express|koa|streamlit|starlette)\b')
RE_CDN = re.compile(r'(?i)(?:src|href)\s*=\s*["\'](https?:)?//(?P<hote>[^/"\']+)(?P<chemin>/[^"\']*)["\']')
RE_LIB_CHEMIN = re.compile(r'/(?:npm/)?(?P<nom>@?[a-z][\w.-]*?)(?:@|/)(?P<v>\d+\.\d+(?:\.\d+)?)(?:/|$)', re.I)
RE_BANNIERE = re.compile(r'/\*!?\s*(?:@license\s+)?(?P<nom>[A-Za-z][\w.\- ]{1,30}?)\s+v?(?P<v>\d+\.\d+\.\d+)\b')
RE_URL = re.compile(r'https?://(?P<hote>[a-z0-9.-]+\.[a-z]{2,})', re.I)
RE_CHARGEMENT = re.compile(r'(?i)(?:<script|<link|<img|<iframe|fetch\(|XMLHttpRequest|\.open\(|requests\.\w+\(|urlopen\(|axios|url\()')
RE_SECRET = re.compile(r'(?i)(password|passwd|mot_de_passe|secret|token|api[_-]?key)["\']?\s*[:=]\s*["\']?([^"\'\s,;]{6,})')
FACTICE = re.compile(r'(?i)(changeme|exemple|example|xxx|\*\*\*|fictif|votre|your|placeholder|os\.environ|process\.env|\$\{|getenv)')
RE_PERSONNES = re.compile(r'(?i)\b(nom_?naissance|pr[ée]nom|date_?(?:de_?)?naissance|nir|num[ée]ro_?s[ée]cu|iban|bic|adresse|'
                          r't[ée]l[ée]phone|courriel|email|nationalit[ée]|handicap|sant[ée]|allocataire|b[ée]n[ée]ficiaire)\b')
RE_VERSION = re.compile(r'(?i)(?:APP_VERSION|\bversion)\s*[:=]\s*["\']?v?(\d+\.\d+(?:\.\d+)?)')
HOTES_IGNORES = {'www.w3.org', 'localhost', 'schemas.openxmlformats.org', 'purl.org', 'schemas.microsoft.com'}


def lire(p: pathlib.Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return p.read_text(encoding='latin-1')
    except OSError:
        return ''


class Releve:
    """Ce que l'on trouve en lisant les fichiers d'un outil."""

    def __init__(self, cible: pathlib.Path):
        self.cible = cible
        self.racine = cible if cible.is_dir() else cible.parent
        self.fichiers = [cible] if cible.is_file() else [p for p in sorted(cible.rglob('*')) if p.is_file()
                                                         and not any(x in IGNORES for x in p.relative_to(cible).parts)]
        self.textes = {p: lire(p) for p in self.fichiers if p.suffix.lower() in EXT_TEXTE and p.stat().st_size < 8_000_000}
        self.composants: dict[tuple[str, str], str] = {}
        self.dependances: list[str] = []
        self.non_figees: list[str] = []

    def rel(self, p: pathlib.Path) -> str:
        return p.relative_to(self.racine).as_posix()

    def code(self) -> dict[pathlib.Path, str]:
        return {p: t for p, t in self.textes.items() if p.suffix.lower() in EXT_CODE}

    # ---------------------------------------------------------------- identité
    def format_probable(self) -> tuple[str, str]:
        noms = {p.name.lower() for p in self.fichiers}
        suffixes = collections.Counter(p.suffix.lower() for p in self.fichiers)
        tout = '\n'.join(t for p, t in self.textes.items() if p.name.startswith('requirements') or p.name == 'package.json')
        if suffixes['.grist']:
            return 'D', 'document Grist présent'
        if noms & {'compose.yaml', 'docker-compose.yml', 'docker-compose.yaml', 'dockerfile'} or CADRICIELS_SERVEUR.search(tout):
            return 'B', 'fichier de conteneur ou cadriciel web côté serveur'
        if suffixes['.wxs'] or suffixes['.spec'] or suffixes['.msi'] or suffixes['.exe'] or 'pyinstaller' in tout.lower():
            return 'C', 'fichiers d\'installation ou d\'exécutable Windows'
        if suffixes['.html'] + suffixes['.htm'] and not suffixes['.py']:
            return 'A', 'pages HTML sans code serveur'
        return '?', 'indéterminé : à confirmer avec la personne'

    def points_entree(self) -> list[str]:
        candidats = ('index.html', 'app.py', 'main.py', 'server.js', 'index.js', 'manage.py', 'serveur.py')
        trouves = [self.rel(p) for p in self.fichiers if p.name.lower() in candidats]
        trouves += [self.rel(p) for p in self.fichiers if p.suffix.lower() in ('.html', '.htm') and p.parent == self.racine][:5]
        return sorted(set(trouves))

    # ---------------------------------------------------------------- dépendances
    def lire_dependances(self) -> None:
        for p, texte in self.textes.items():
            if re.fullmatch(r'requirements[\w.-]*\.txt', p.name):
                self._requirements(p, texte)
            elif p.name == 'package.json':
                self._package(p, texte)
            elif p.name.lower() == 'dockerfile' or p.name.endswith(('compose.yaml', 'compose.yml')):
                for image in re.findall(r'(?im)^\s*(?:FROM|image:)\s+(\S+)', texte):
                    nom, _, version = image.partition(':')
                    self.composants.setdefault((nom.split('/')[-1], version or '?'), f'image ({self.rel(p)})')

    def _requirements(self, p: pathlib.Path, texte: str) -> None:
        for ligne in texte.splitlines():
            ligne = ligne.split('#', 1)[0].strip()
            if not ligne or ligne.startswith('-'):
                continue
            nom = re.split(r'[=<>~!\[; ]', ligne, maxsplit=1)[0]
            version = ligne.split('==', 1)[1].split(';')[0].strip() if '==' in ligne else '?'
            self.dependances.append(f'{ligne} ({self.rel(p)})')
            self.composants.setdefault((nom, version), f'bibliothèque Python ({self.rel(p)})')
            if '==' not in ligne:
                self.non_figees.append(f'{ligne} ({self.rel(p)})')

    def _package(self, p: pathlib.Path, texte: str) -> None:
        try:
            contenu = json.loads(texte)
        except json.JSONDecodeError:
            self.dependances.append(f'{self.rel(p)} illisible')
            return
        for nom, version in {**contenu.get('dependencies', {}), **contenu.get('devDependencies', {})}.items():
            self.dependances.append(f'{nom} {version} ({self.rel(p)})')
            self.composants.setdefault((nom, str(version).lstrip('^~')), f'bibliothèque JavaScript ({self.rel(p)})')
            if not re.fullmatch(r'\d+\.\d+\.\d+', str(version)):
                self.non_figees.append(f'{nom} {version} ({self.rel(p)})')
        if not (p.parent / 'package-lock.json').exists() and contenu.get('dependencies'):
            self.non_figees.append(f'{self.rel(p)} sans package-lock.json')

    def bibliotheques_web(self) -> None:
        for p, texte in self.code().items():
            for m in RE_CDN.finditer(texte):
                lib = RE_LIB_CHEMIN.search(m.group('chemin'))
                if lib and m.group('hote') not in HOTES_IGNORES:
                    self.composants.setdefault((lib.group('nom'), lib.group('v')), f'chargée depuis {m.group("hote")} ({self.rel(p)})')
            for m in RE_BANNIERE.finditer(texte[:2_000_000]):
                nom = m.group('nom').strip()
                if len(nom) > 2 and not nom.lower().startswith(('copyright', 'version', 'license')):
                    self.composants.setdefault((nom, m.group('v')), f'embarquée ({self.rel(p)})')

    # ---------------------------------------------------------------- risques
    def appels_externes(self) -> dict[str, dict[str, set[str]]]:
        hotes: dict[str, dict[str, set[str]]] = collections.defaultdict(lambda: {'chargement': set(), 'mention': set()})
        for p, texte in self.code().items():
            for ligne in texte.splitlines():
                for m in RE_URL.finditer(ligne[:5000]):
                    hote = m.group('hote').lower()
                    if hote not in HOTES_IGNORES:
                        nature = 'chargement' if RE_CHARGEMENT.search(ligne) else 'mention'
                        hotes[hote][nature].add(self.rel(p))
        return dict(hotes)

    def secrets(self) -> list[str]:
        trouves = []
        for p, texte in self.textes.items():
            if p.suffix.lower() == '.md':
                continue
            for numero, ligne in enumerate(texte.splitlines(), 1):
                m = RE_SECRET.search(ligne[:3000])
                if m and not FACTICE.search(ligne):
                    valeur = m.group(2)
                    trouves.append(f'{self.rel(p)}:{numero} — « {m.group(1)} » = {valeur[:2]}{"•" * 6} (valeur masquée)')
        if any(p.name == '.env' for p in self.fichiers):
            trouves.append('fichier .env présent : contient probablement des secrets réels (ne pas l\'ouvrir dans la conversation)')
        return trouves

    def donnees_personnes(self) -> list[str]:
        mots: dict[str, set[str]] = collections.defaultdict(set)
        for p, texte in self.code().items():
            for m in RE_PERSONNES.finditer(texte[:2_000_000]):
                mots[m.group(1).lower()].add(self.rel(p))
        return [f'« {mot} » dans {", ".join(sorted(f)[:3])}' for mot, f in sorted(mots.items())]

    def versions(self) -> list[str]:
        trouvees = []
        if (self.racine / 'VERSION').exists():
            trouvees.append(f'VERSION : {lire(self.racine / "VERSION").strip()}')
        for p, texte in self.code().items():
            for m in RE_VERSION.finditer(texte[:200_000]):
                trouvees.append(f'{self.rel(p)} : {m.group(1)}')
                break
        return trouvees[:10]

    def dossier(self) -> tuple[list[str], list[str]]:
        presents = [e for e in DOSSIER_FABRIQUE if (self.racine / e.rstrip('/')).exists()]
        return presents, [e for e in DOSSIER_FABRIQUE if e not in presents]


def puces(elements: list[str], vide: str = 'rien de repéré') -> list[str]:
    return [f'- {e}' for e in elements] or [f'- {vide}']


def rediger(releve: Releve) -> str:
    releve.lire_dependances()
    releve.bibliotheques_web()
    lettre, raison = releve.format_probable()
    presents, manquants = releve.dossier()
    dates = [datetime.date.fromtimestamp(p.stat().st_mtime) for p in releve.fichiers]
    taille = sum(p.stat().st_size for p in releve.fichiers)
    types = collections.Counter(p.suffix.lower() or '(sans extension)' for p in releve.fichiers)
    hotes = releve.appels_externes()
    lignes = [f'# Relevé de l\'outil « {releve.cible.name} »', '',
              f'Relevé automatique du {datetime.date.today().isoformat()}. Un relevé lit les fichiers : il se trompe parfois, tout est à vérifier.', '',
              '## Identité', f'- Fichiers : {len(releve.fichiers)} ({taille // 1024} Ko) ; types : ' + ', '.join(f'{e} ({n})' for e, n in types.most_common(8)),
              f'- Dernière modification d\'un fichier : {max(dates).isoformat() if dates else "?"}',
              f'- Format probable : **{lettre}** ({raison})', '- Points d\'entrée : ' + (', '.join(releve.points_entree()) or 'non repérés'), '',
              '## Versions annoncées', *puces(releve.versions(), 'aucune : la version n\'est pas connue'), '',
              '## Dépendances déclarées', *puces(releve.dependances, 'aucune déclarée'), '',
              '## Dépendances non figées', *puces(releve.non_figees, 'aucune'), '',
              '## Ressources chargées depuis Internet']
    chargements = [f'{h} ({", ".join(sorted(v["chargement"])[:3])})' for h, v in sorted(hotes.items()) if v['chargement']]
    mentions = [h for h, v in sorted(hotes.items()) if v['mention'] and not v['chargement']]
    lignes += puces(chargements, 'aucune') + [f'- Simples mentions d\'adresses (liens, commentaires) : {", ".join(mentions[:10]) or "aucune"}', '',
                                              '## Secrets possibles (valeurs masquées)', *puces(releve.secrets(), 'aucun repéré'), '',
                                              '## Données de personnes possibles (mots repérés dans le code)', *puces(releve.donnees_personnes(), 'aucun mot repéré'), '',
                                              '## Dossier', f'- Présent : {", ".join(presents) or "rien"}', f'- Manquant : {", ".join(manquants) or "rien"}', '',
                                              '## Composants à vérifier (à reprendre dans docs/composants.md)', '',
                                              '| Composant | Version | Rôle | Fin de support | Source de la date |', '|---|---|---|---|---|']
    lignes += [f'| {nom} | {version} | {role} | À COMPLÉTER | À COMPLÉTER |' for (nom, version), role in sorted(releve.composants.items())] \
        or ['| À COMPLÉTER | À COMPLÉTER | À COMPLÉTER | À COMPLÉTER | À COMPLÉTER |']
    lignes += ['', '## Priorités proposées',
               '1. Sûreté : secrets ci-dessus à renouveler et à sortir du code ; ressources chargées depuis Internet à embarquer ou à déclarer ; données de personnes à confirmer.',
               '2. Composants : vérifier en ligne la date de fin de support de chacun.',
               '3. Dossier : `remettre_a_niveau.py` pour ajouter ce qui manque, puis tests de caractérisation.']
    return '\n'.join(lignes) + '\n'


def main(argv: list[str]) -> int:
    analyseur = argparse.ArgumentParser(prog='releve_outil.py', description='Relevé d\'un outil existant, sans le modifier.')
    analyseur.add_argument('cible', help='dossier ou fichier de l\'outil (de préférence une copie)')
    analyseur.add_argument('--sortie', help='fichier Markdown à écrire (par défaut : releve-<nom>.md dans le dossier courant)')
    options = analyseur.parse_args(argv)
    cible = pathlib.Path(options.cible).resolve()
    if not cible.exists():
        sys.exit(f'Arrêt : introuvable : {cible}')
    sortie = pathlib.Path(options.sortie) if options.sortie else pathlib.Path.cwd() / f'releve-{cible.stem}.md'
    texte = rediger(Releve(cible))
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding='utf-8')
    print(f'Relevé écrit : {sortie}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
