"""Contrôle un projet d'outil, écrit le dossier de transmission pour la cellule et fabrique le paquet (zip) si tout est cohérent.

Deux niveaux (ligne « Niveau : » du README) :
  partagé   un fichier HTML pour des collègues : seul le socle de sûreté est exigé (secrets, appels externes, code dangereux,
            tests en échec s'il y en a) ; tout le reste est une recommandation ;
  durable   un outil destiné à être installé : socle complet, documentation, tests, composants.
Le contrôle ne vous empêche jamais d'utiliser votre outil : il dit ce qu'il manque pour que la cellule puisse l'installer.

Usage : python3 fabriquer.py [dossier_du_projet] [options]      (python3 fabriquer.py --help pour les options)

Bibliothèque standard uniquement (Python 3.9 ou plus). Code de sortie : 0 si aucune erreur, 1 sinon.
Tout ce qui est contrôlé, réussi, refusé ou non testé est écrit en clair dans dist/bilan-fabrication.md.

Ce que le script contrôle :
  1. fichiers obligatoires présents ; champs « À COMPLÉTER » restants ;
  2. un seul numéro de version partout (VERSION, README, CHANGELOG, docs, APP_VERSION, package.json) ;
  3. chaque règle de gestion RG-xx de la SPEC a un test ET une mention dans le code ; SPEC validée ;
  4. **les tests sont exécutés et doivent passer** (pytest s'il est installé, sinon un lanceur intégré ; node pour les tests JavaScript) ;
  5. le code : syntaxe Python et JavaScript, motifs dangereux (eval, shell=True, SQL construit…), erreurs avalées en silence ;
  6. aucun secret en dur, aucun fichier .env dans le dossier ;
  7. aucun appel réseau sortant hors de la liste déclarée et motivée dans reseau-autorise.txt ;
  8. dépendances figées (requirements, package-lock, Dockerfile) ;
  9. analyses quand les outils sont installés : ruff, bandit, pip-audit, npm audit, gitleaks, trivy (sur demande) ;
 10. (format B) compose et vhost conformes au socle ; essai de restauration noté ;
 11. composants listés, avec une date de fin de support non dépassée ;
 12. exceptions à revoir, changements de périmètre non validés, décisions techniques notées ;
 13. outil réutilisable pas encore signalé à la cellule opérationnelle (alerte amicale, jamais bloquante) ;
 14. rôle d'éditeur : contrat d'entrée (un exemple par format reçu), fiche rustine à revoir, questions-tests des fonctions
     d'IA, mention de traçabilité sur les documents produits. Ce sont des exigences de complétude ou des alertes :
     elles ne bloquent jamais un brouillon ni un outil partagé.

Marqueurs reconnus dans le code : « nosecret » (exemple fictif de secret) et « nosec » (motif dangereux justifié),
toujours suivis de la raison sur la même ligne.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import dataclasses
import datetime
import fnmatch
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

Chemin = pathlib.Path

MARQUEUR = 'À COMPLÉTER'
RE_MARQUEUR = re.compile(r'À[ _-]?COMPLÉTER')
EXTENSIONS_TEXTE = {'.py', '.js', '.mjs', '.cjs', '.ts', '.html', '.htm', '.css', '.md', '.txt', '.json', '.yaml', '.yml',
                    '.ini', '.conf', '.sh', '.ps1', '.cfg', '.toml', '.xml', '.csv', '.exemple', '.env', '.vue', ''}
DOSSIERS_IGNORES = {'.git', 'node_modules', 'dist', '__pycache__', 'data', '.venv', 'venv', 'vendor', '.pytest_cache',
                    '.ruff_cache'}
DOSSIERS_HORS_CODE = {'docs', 'tests', 'build'}          # ni motifs dangereux ni analyse de style
EXCLUS_PAQUET = ['.env', '.env.*', '*.env', 'dist', '__pycache__', '*.pyc', 'data', 'node_modules', '.git', '.DS_Store',
                 'donnees-reelles', '*.sqlite', '*.db', '.pytest_cache', '.ruff_cache']
FICHIERS_ENV_AUTORISES = {'.env.exemple', '.env.example'}
LIGNE_MINIFIEE = 2000            # au-delà, la ligne est une bibliothèque embarquée : elle relève de composants.md
FONCTION_LONGUE = 80
MODULE_PRISE_EN_MAIN = {'prise-en-main.js'}
OBLIGATOIRES = ['README.md', 'SPEC.md', 'CHANGELOG.md', 'VERSION', '.gitignore', 'reseau-autorise.txt',
                'docs/grille-vigilance.md', 'docs/recette.md', 'docs/composants.md', 'docs/derogations.md',
                'docs/perimetre.md', 'docs/exploitation.md', 'docs/fiche-dsi.md']
OBLIGATOIRES_B = ['deploy/.env.exemple', 'deploy/procedure-installation.md']
# Niveau « partagé » : un HTML utilisé par quelques collègues. Socle minimal pour tous, le reste vient avec le niveau durable.
OBLIGATOIRES_PARTAGE = ['README.md', 'SPEC.md', 'CHANGELOG.md', 'VERSION', '.gitignore', 'reseau-autorise.txt', 'docs/partage.md']
NIVEAU_PARTAGE = 'partagé'
VERSION_CONTROLE = '1.1'   # version de ce contrôle : la revue des outils repère les dossiers qui en embarquent une ancienne
FICHIERS_DE_SURETE = {'README.md', 'VERSION', '.gitignore', 'reseau-autorise.txt'}   # sans eux, les contrôles de sûreté ne peuvent pas tourner
NIVEAU_DURABLE = 'durable'


# ================================================================ bilan et contexte
@dataclasses.dataclass
class Bilan:
    """Résultat des contrôles, dans l'ordre où ils sont faits."""
    erreurs: list[str] = dataclasses.field(default_factory=list)
    alertes: list[str] = dataclasses.field(default_factory=list)
    ok: list[str] = dataclasses.field(default_factory=list)
    non_testes: list[str] = dataclasses.field(default_factory=list)

    def erreur(self, message: str) -> None:
        self.erreurs.append(message)

    def alerte(self, message: str) -> None:
        self.alertes.append(message)

    def reussi(self, message: str) -> None:
        self.ok.append(message)

    def non_teste(self, message: str) -> None:
        self.non_testes.append(message)


@dataclasses.dataclass
class Contexte:
    """Tout ce dont un contrôle a besoin : le projet, les options et le bilan."""
    racine: Chemin
    format: str
    brouillon: bool
    aujourdhui: datetime.date
    exiger_analyses: bool
    sans_tests: bool
    analyser_images: bool
    delai: int
    niveau: str = NIVEAU_DURABLE
    bilan: Bilan = dataclasses.field(default_factory=Bilan)
    version: str | None = None
    images: list[str] = dataclasses.field(default_factory=list)
    _textes: dict[Chemin, str | None] = dataclasses.field(default_factory=dict)

    def texte(self, chemin: Chemin) -> str | None:
        """Contenu d'un fichier texte, lu une seule fois ; None s'il est absent ou illisible."""
        if chemin not in self._textes:
            try:
                self._textes[chemin] = chemin.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                self._textes[chemin] = None
        return self._textes[chemin]

    def oublier(self, chemin: Chemin) -> None:
        self._textes.pop(chemin, None)

    def rel(self, chemin: Chemin) -> str:
        return chemin.relative_to(self.racine).as_posix()

    def fichiers(self, sous_dossier: str | None = None, extensions: set[str] | None = None) -> list[Chemin]:
        """Fichiers texte du projet, hors dossiers ignorés, hors gros fichiers et hors le script de contrôle lui-même."""
        base = self.racine / sous_dossier if sous_dossier else self.racine
        if not base.exists():
            return []
        if base.is_file():
            return [base] if self._retenu(base, extensions) else []
        return [p for p in sorted(base.rglob('*')) if self._retenu(p, extensions)]

    def _retenu(self, p: Chemin, extensions: set[str] | None) -> bool:
        if not p.is_file() or any(part in DOSSIERS_IGNORES for part in p.relative_to(self.racine).parts):
            return False
        if p.stat().st_size > 5_000_000 or (p.name == 'fabriquer.py' and p.parent.name == 'build'):
            return False
        suffixe = p.suffix.lower()
        if extensions is not None and suffixe not in extensions:
            return False
        return suffixe in EXTENSIONS_TEXTE or p.name.startswith('.env')

    def fichiers_code(self, extensions: set[str]) -> list[Chemin]:
        """Le code de l'outil : tout sauf la documentation, les tests et le dossier build/."""
        return [p for p in self.fichiers(extensions=extensions)
                if p.relative_to(self.racine).parts[0] not in DOSSIERS_HORS_CODE]

    @property
    def souple(self) -> bool:
        """Brouillon ou niveau partagé : la complétude est recommandée, pas exigée. Le socle de sûreté reste exigé."""
        return self.brouillon or self.niveau == NIVEAU_PARTAGE

    def exiger(self, message: str) -> None:
        """Exigence de complétude : bloquante pour une livraison durable, simple alerte en brouillon ou niveau partagé."""
        (self.bilan.alerte if self.souple else self.bilan.erreur)(message)

    def outil_absent(self, outil: str, role: str) -> None:
        """Analyse impossible faute d'outil : « non testé », ou erreur si les analyses sont exigées."""
        if self.exiger_analyses:
            self.bilan.erreur(f'Analyse exigée mais « {outil} » n\'est pas installé ({role})')
        else:
            self.bilan.non_teste(f'« {outil} » absent — non fait : {role}')

    def derogation_notee(self, *mots: str) -> bool:
        texte = (self.texte(self.racine / 'docs' / 'derogations.md') or '').lower()
        return any(mot.lower() in texte for mot in mots)


# ================================================================ petits outils
def lancer(commande: list[str], dossier: Chemin, delai: int, env_plus: dict[str, str] | None = None) -> tuple[int | None, str]:
    """Lance une commande sans interpréteur de commandes. Retourne (code, sortie) ; code None si elle n'a pas pu tourner."""
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1', **(env_plus or {})}
    try:
        res = subprocess.run(commande, cwd=dossier, capture_output=True, text=True, encoding='utf-8', errors='replace',
                             timeout=delai, env=env, check=False)
    except subprocess.TimeoutExpired:
        return None, f'délai de {delai} s dépassé'
    except OSError as erreur:
        return None, str(erreur)
    return res.returncode, (res.stdout + '\n' + res.stderr).strip()


def fin_de_sortie(sortie: str, lignes: int = 8, largeur: int = 700) -> str:
    """Les dernières lignes d'une sortie de commande, sur une seule ligne lisible dans le bilan."""
    utiles = [ligne.strip() for ligne in sortie.splitlines() if ligne.strip()]
    return ' ⏎ '.join(utiles[-lignes:])[-largeur:]


def lignes_tableau(texte: str) -> list[list[str]]:
    """Lignes d'un tableau Markdown, sans l'en-tête ni la ligne de séparation."""
    lignes = []
    for ligne in texte.splitlines():
        brut = ligne.strip()
        if brut.startswith('|') and not re.match(r'^\|[\s:|-]+\|?$', brut):
            lignes.append([case.strip() for case in brut.strip('|').split('|')])
    return lignes[1:]


def lire_date(valeur: str) -> datetime.date | None:
    """AAAA-MM-JJ, AAAA-MM (dernier jour du mois) ou JJ/MM/AAAA ; None si illisible."""
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


def champ_fiche(texte: str, libelle: str) -> str | None:
    """Valeur d'une ligne « - Libellé (…) : valeur » ; chaîne vide si rien n'est saisi ; None si la ligne est absente."""
    m = re.search(rf'(?im)^[ \t]*[-*][ \t]*{libelle}[^:\n]*:[ \t]*(.*)$', texte)
    return m.group(1).strip() if m else None


def a_completer(valeur: str | None) -> bool:
    return valeur is None or not valeur or bool(RE_MARQUEUR.search(valeur))


# ================================================================ 1. fichiers obligatoires et champs à compléter
def controle_fichiers(ctx: Contexte) -> None:
    if ctx.niveau == NIVEAU_PARTAGE:
        attendus = OBLIGATOIRES_PARTAGE
    else:
        attendus = OBLIGATOIRES + (OBLIGATOIRES_B if ctx.format == 'B' else [])
    manquants = [f for f in attendus if not (ctx.racine / f).exists()]
    for fichier in manquants:
        if fichier in FICHIERS_DE_SURETE:
            ctx.bilan.erreur(f'Fichier obligatoire absent : {fichier}')
        else:
            ctx.exiger(f'Document absent : {fichier} (nécessaire pour une installation par la cellule)')
    if not manquants:
        ctx.bilan.reussi('Tous les fichiers obligatoires sont présents')
    restants = []
    for p in ctx.fichiers(extensions={'.md', '.yaml', '.yml', '.txt', '.conf'}):
        nombre = len(RE_MARQUEUR.findall(ctx.texte(p) or ''))
        if nombre:
            restants.append(f'{ctx.rel(p)} ({nombre})')
    if restants:
        ctx.exiger(f'Champs « {MARQUEUR} » restants : ' + ', '.join(restants))
    else:
        ctx.bilan.reussi(f'Aucun champ « {MARQUEUR} » restant')


# ================================================================ 2. version unique
RE_VERSION_DOC = re.compile(r'(?im)^.*\bVersion(?: documentée)?\s*:\s*\**\s*(\d+\.\d+\.\d+)')
RE_APP_VERSION = re.compile(r'APP_VERSION\s*[:=]\s*[\'"](\d+\.\d+\.\d+)[\'"]')


def ecarts_documents(ctx: Contexte, version: str) -> list[str]:
    ecarts = []
    cibles = [ctx.racine / 'README.md', *sorted((ctx.racine / 'docs').glob('*.md')), *sorted((ctx.racine / 'deploy').glob('*.md'))]
    for p in cibles:
        texte = ctx.texte(p)
        if texte is None:
            continue
        m = RE_VERSION_DOC.search(texte)
        if not m:
            ecarts.append(f'{ctx.rel(p)} : aucune ligne « Version : x.y.z »')
        elif m.group(1) != version:
            ecarts.append(f'{ctx.rel(p)} : {m.group(1)} au lieu de {version}')
    m = re.search(r'(?m)^##\s*\[?(\d+\.\d+\.\d+)\]?', ctx.texte(ctx.racine / 'CHANGELOG.md') or '')
    if not m:
        ecarts.append('CHANGELOG.md : aucune entrée de version')
    elif m.group(1) != version:
        ecarts.append(f'CHANGELOG.md : première entrée {m.group(1)} au lieu de {version}')
    return ecarts


def ecarts_code(ctx: Contexte, version: str) -> tuple[list[str], int]:
    ecarts, constantes = [], 0
    for p in ctx.fichiers(extensions={'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.json', '.yaml', '.yml'}):
        if p.name == 'package-lock.json':
            continue
        texte = ctx.texte(p) or ''
        for m in RE_APP_VERSION.finditer(texte):
            constantes += 1
            if m.group(1) != version:
                ecarts.append(f'{ctx.rel(p)} : APP_VERSION = {m.group(1)} au lieu de {version}')
        m = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', texte) if p.name == 'package.json' else None
        if m and m.group(1) != version:
            ecarts.append(f'package.json : {m.group(1)} au lieu de {version}')
    return ecarts, constantes


def controle_version(ctx: Contexte) -> None:
    version = (ctx.texte(ctx.racine / 'VERSION') or '').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        ctx.bilan.erreur(f'VERSION doit contenir x.y.z (trouvé : « {version} »)')
        return
    ctx.version = version
    spec = re.search(r'(?m)^#\s*SPEC.*?\bv(\d+)\.(\d+)', ctx.texte(ctx.racine / 'SPEC.md') or '')
    if spec and f'{spec.group(1)}.{spec.group(2)}' != '.'.join(version.split('.')[:2]):
        ctx.bilan.alerte(f'SPEC.md annonce v{spec.group(1)}.{spec.group(2)} alors que la version de l\'outil est {version}')
    ecarts_du_code, constantes = ecarts_code(ctx, version)
    if not constantes:
        ctx.bilan.alerte('Aucune constante APP_VERSION dans le code : la version affichée par l\'application n\'est pas contrôlée')
    ecarts = ecarts_documents(ctx, version) + ecarts_du_code
    for ecart in ecarts:
        ctx.exiger('Version non alignée — ' + ecart)
    if not ecarts:
        ctx.bilan.reussi(f'Version {version} identique partout')


# ================================================================ 3. règles de gestion
RE_RG_DEF = re.compile(r'(?m)^\s*[-*]\s*\**\s*(RG-\d+)\s*\**\s*[—–-]\s*(.*)$')


def emplacements_code(ctx: Contexte) -> list[str]:
    """Où est le code : src/ par défaut ; pour un outil repris, ce que déclare build/controles.json : {"code": ["index.html"]}."""
    fichier = ctx.racine / 'build' / 'controles.json'
    if fichier.exists():
        try:
            declares = json.loads(ctx.texte(fichier) or '{}').get('code')
        except (json.JSONDecodeError, AttributeError):
            declares = None
        if isinstance(declares, list) and declares:
            return [str(d).strip('/') for d in declares if str(d).strip('/') and not str(d).startswith('..')]
    return ['src']


def contenu_sans_doc(ctx: Contexte, dossier: str, extensions: set[str] | None = None) -> str:
    """Le texte du code ou des tests : la documentation (.md, .txt) ne compte pas comme une mention."""
    return '\n'.join(ctx.texte(p) or '' for p in ctx.fichiers(dossier, extensions) if p.suffix.lower() not in ('.md', '.txt'))


def controle_regles(ctx: Contexte) -> None:
    spec = ctx.texte(ctx.racine / 'SPEC.md') or ''
    definitions = {m.group(1): m.group(2) for m in RE_RG_DEF.finditer(spec)}
    actives = [rg for rg, texte in definitions.items() if 'supprimée' not in texte.lower() and '<' not in texte[:3]]
    if not actives:
        ctx.exiger('SPEC.md : aucune règle de gestion « - RG-01 — … » trouvée (recommandé dès qu\'il y a un calcul ou un tri)')
        return
    code = '\n'.join(contenu_sans_doc(ctx, d) for d in emplacements_code(ctx)) + '\n' + contenu_sans_doc(ctx, 'deploy', {'.py', '.js', '.sh', '.ps1'})
    tests = contenu_sans_doc(ctx, 'tests')
    sans_test = [rg for rg in actives if not re.search(rf'\b{re.escape(rg)}\b', tests)]
    sans_code = [rg for rg in actives if not re.search(rf'\b{re.escape(rg)}\b', code)]
    if sans_test:
        ctx.exiger('Règles sans test dans tests/ : ' + ', '.join(sans_test))
    if sans_code:
        ctx.exiger(f'Règles jamais citées dans le code ({", ".join(emplacements_code(ctx))}) : ' + ', '.join(sans_code))
    inconnues = sorted(set(re.findall(r'\bRG-\d+\b', code + '\n' + tests)) - set(definitions))
    if inconnues:
        ctx.bilan.alerte('Règles citées dans le code ou les tests mais absentes de la SPEC : ' + ', '.join(inconnues))
    if not sans_test and not sans_code:
        ctx.bilan.reussi(f'{len(actives)} règle(s) de gestion : chacune a un test et une mention dans le code')
    statut = re.search(r'(?im)^Statut\s*:\s*(.*)$', spec)
    if statut and statut.group(1).strip().lower().startswith('validée'):
        ctx.bilan.reussi('SPEC validée')
    else:
        ctx.exiger('SPEC.md : le statut n\'est pas « validée le JJ/MM/AAAA par … »')


# ================================================================ 4. exécution des tests
MINI_LANCEUR = r'''
import runpy, sys, traceback
total = echecs = 0
for chemin in sys.argv[1:]:
    try:
        espace = runpy.run_path(chemin, run_name="__test__")
    except BaseException:
        echecs += 1
        print("ÉCHEC au chargement de", chemin)
        traceback.print_exc()
        continue
    for nom, objet in sorted(espace.items()):
        if nom.startswith("test_") and callable(objet):
            total += 1
            try:
                objet()
            except BaseException:
                echecs += 1
                print("ÉCHEC", chemin, nom)
                traceback.print_exc()
print(f"{total} test(s) exécuté(s), {echecs} échec(s)")
sys.exit(1 if echecs else (5 if total == 0 else 0))
'''
AUCUN_TEST = 5                    # code de sortie de pytest et du lanceur intégré quand aucun test n'a tourné


def fichiers_tests(ctx: Contexte, *motifs: str) -> list[str]:
    base = ctx.racine / 'tests'
    trouves = {p for motif in motifs for p in base.rglob(motif)} if base.exists() else set()
    return sorted(ctx.rel(p) for p in trouves if not any(part in DOSSIERS_IGNORES for part in p.relative_to(ctx.racine).parts))


def commandes_declarees(ctx: Contexte) -> list[list[str]] | None:
    """Commandes de test écrites dans build/controles.json : {"tests": [["python3", "-m", "pytest", "tests"]]}."""
    fichier = ctx.racine / 'build' / 'controles.json'
    if not fichier.exists():
        return None
    try:
        declarees = json.loads(ctx.texte(fichier) or '').get('tests')
    except (json.JSONDecodeError, AttributeError):
        ctx.bilan.erreur('build/controles.json illisible : attendu {"tests": [["commande", "argument", …]]}')
        return []
    if not isinstance(declarees, list) or not declarees:
        return None
    return [shlex.split(c) if isinstance(c, str) else [str(x) for x in c] for c in declarees]


def commandes_tests(ctx: Contexte) -> list[list[str]]:
    declarees = commandes_declarees(ctx)
    if declarees is not None:
        return declarees
    commandes: list[list[str]] = []
    python = fichiers_tests(ctx, 'test_*.py', '*_test.py')
    if python and importlib.util.find_spec('pytest'):
        commandes.append([sys.executable, '-m', 'pytest', '-q', '--no-header', '-p', 'no:cacheprovider', 'tests'])
    elif python:
        commandes.append([sys.executable, '-c', MINI_LANCEUR, *python])
    node_test = fichiers_tests(ctx, '*.test.js', '*.test.mjs', '*.test.cjs')
    if node_test:
        commandes.append(['node', '--test', *node_test])
    scripts = fichiers_tests(ctx, 'test_*.js', 'test_*.mjs', 'essai_*.js', 'essai_*.mjs')
    commandes += [['node', f] for f in scripts if f not in node_test]
    return commandes


def lancer_un_test(ctx: Contexte, commande: list[str], journal: list[str]) -> bool:
    lisible = ' '.join('<lanceur intégré>' if c == MINI_LANCEUR else c for c in commande)
    if commande[0] == 'node' and not shutil.which('node'):
        ctx.exiger(f'Tests JavaScript non exécutés : « node » n\'est pas installé ({lisible})')
        return False
    code, sortie = lancer(commande, ctx.racine, ctx.delai, {'PYTHONPATH': str(ctx.racine)})
    journal.append(f'$ {lisible}\n{sortie}\n')
    if code == 0:
        return True
    if code == AUCUN_TEST:
        ctx.exiger(f'Aucun test n\'a tourné ({lisible}) : écrire les tests sous forme de fonctions « test_… »')
        return False
    raison = 'n\'a pas pu tourner' if code is None else 'en échec'
    ctx.bilan.erreur(f'Tests {raison} — {lisible} : {fin_de_sortie(sortie)} (détail : dist/tests-sortie.txt)')
    return False


def controle_tests(ctx: Contexte) -> None:
    if ctx.sans_tests:
        ctx.bilan.non_teste('Tests non exécutés (option --sans-tests)')
        if not ctx.souple:
            ctx.bilan.erreur('Une livraison exige des tests exécutés : --sans-tests n\'est accepté qu\'avec --brouillon (ou en niveau partagé)')
        return
    commandes = commandes_tests(ctx)
    if not commandes:
        if ctx.format == 'D':
            ctx.bilan.non_teste('Format D (Grist) : pas de test exécutable attendu ; la recette métier fait foi')
        else:
            ctx.exiger('Aucun test exécutable dans tests/ (attendus : test_*.py, *.test.js, test_*.js ou essai_*.js)')
        return
    journal: list[str] = []
    reussis = sum(lancer_un_test(ctx, commande, journal) for commande in commandes)
    (ctx.racine / 'dist').mkdir(exist_ok=True)
    (ctx.racine / 'dist' / 'tests-sortie.txt').write_text('\n'.join(journal), encoding='utf-8')
    if reussis == len(commandes):
        ctx.bilan.reussi(f'Tests exécutés : {len(commandes)} commande(s), aucun échec')


# ================================================================ 5. code : syntaxe, motifs dangereux, erreurs avalées
MOTIFS_PYTHON = [
    (re.compile(r'(?<![\w.])(?:eval|exec)\('), 'eval() ou exec() : exécution de code à partir d\'un texte', True),
    (re.compile(r'shell\s*=\s*True'), 'shell=True : commande système construite (risque d\'injection)', True),
    (re.compile(r'\bos\.(?:system|popen)\('), 'os.system() ou os.popen() : préférer subprocess avec une liste d\'arguments', True),
    (re.compile(r'\bpickle\.loads?\('), 'pickle : ne jamais relire un fichier reçu avec pickle', True),
    (re.compile(r'\byaml\.load\((?!.*Safe)'), 'yaml.load sans SafeLoader : utiliser yaml.safe_load', True),
    (re.compile(r'verify\s*=\s*False'), 'verify=False : vérification du certificat désactivée', True),
    (re.compile(r'\.execute(?:many)?\(\s*f["\']|\.execute(?:many)?\([^)\n]*["\']\s+(?:%|\+)\s*\w'),
     'requête SQL construite avec du texte : utiliser une requête paramétrée', True),
    (re.compile(r'\bdebug\s*=\s*True'), 'debug=True : mode débogage à ne pas livrer', False),
    (re.compile(r'\betree\.(?:parse|fromstring|XML)\((?!.*parser\s*=)'),
     'lecture XML d\'un fichier reçu : désactiver les entités externes (XMLParser(resolve_entities=False, no_network=True)) ou utiliser defusedxml', False),
    (re.compile(r'\bhashlib\.(?:md5|sha1)\('), 'md5 ou sha1 : à ne pas utiliser pour la sécurité', False),
]
MOTIFS_WEB = [
    (re.compile(r'(?<![\w.])eval\('), 'eval() : exécution de code à partir d\'un texte', True),
    (re.compile(r'\bnew\s+Function\('), 'new Function() : exécution de code à partir d\'un texte', True),
    (re.compile(r'\bdocument\.write\('), 'document.write() : à remplacer par la création d\'éléments', True),
    (re.compile(r'\bset(?:Timeout|Interval)\(\s*["\']'), 'setTimeout ou setInterval avec un texte : passer une fonction', False),
]
RE_HTML_DYNAMIQUE = re.compile(r'\.(?:innerHTML|outerHTML)\s*\+?=|\.insertAdjacentHTML\(')
RE_STOCKAGE = re.compile(r'\b(?:localStorage|sessionStorage)\.setItem\(|\bindexedDB\.open\(')
EXT_PYTHON = {'.py'}
EXT_WEB = {'.js', '.mjs', '.cjs', '.ts', '.html', '.htm', '.vue'}


class VisiteurPython(ast.NodeVisitor):
    """Repère ce qu'une relecture attentive relèverait : erreurs avalées et fonctions trop longues."""

    def __init__(self, lignes: list[str]):
        self.lignes = lignes
        self.erreurs: list[str] = []
        self.alertes: list[str] = []

    def visit_ExceptHandler(self, noeud: ast.ExceptHandler) -> None:
        commentee = '#' in self.lignes[noeud.lineno - 1] or (noeud.body and '#' in self.lignes[noeud.body[0].lineno - 1])
        if noeud.type is None:
            self.erreurs.append(f'ligne {noeud.lineno} : « except: » sans type (attrape tout, y compris l\'arrêt du programme)')
        elif len(noeud.body) == 1 and isinstance(noeud.body[0], ast.Pass) and not commentee:
            self.alertes.append(f'ligne {noeud.lineno} : erreur avalée en silence (« pass ») sans commentaire qui dise pourquoi')
        self.generic_visit(noeud)

    def _fonction(self, noeud: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        longueur = (noeud.end_lineno or noeud.lineno) - noeud.lineno + 1
        if longueur > FONCTION_LONGUE:
            self.alertes.append(f'ligne {noeud.lineno} : fonction « {noeud.name} » de {longueur} lignes (à découper)')
        self.generic_visit(noeud)

    visit_FunctionDef = _fonction
    visit_AsyncFunctionDef = _fonction


def analyse_python(ctx: Contexte) -> None:
    fichiers = ctx.fichiers(extensions=EXT_PYTHON)
    if not fichiers:
        return
    fautes = 0
    for p in fichiers:
        texte = ctx.texte(p) or ''
        try:
            arbre = ast.parse(texte, filename=str(p))
        except SyntaxError as erreur:
            fautes += 1
            ctx.bilan.erreur(f'Erreur de syntaxe Python — {ctx.rel(p)}:{erreur.lineno} : {erreur.msg}')
            continue
        if p.relative_to(ctx.racine).parts[0] in DOSSIERS_HORS_CODE:
            continue
        visiteur = VisiteurPython(texte.splitlines())
        visiteur.visit(arbre)
        for message in visiteur.erreurs:
            fautes += 1
            ctx.bilan.erreur(f'Code — {ctx.rel(p)}, {message}')
        for message in visiteur.alertes:
            ctx.bilan.alerte(f'Code — {ctx.rel(p)}, {message}')
    if not fautes:
        ctx.bilan.reussi(f'Python : syntaxe correcte, aucune erreur avalée sans type ({len(fichiers)} fichier(s))')


def chercher_motifs(ctx: Contexte, extensions: set[str], motifs: list) -> tuple[int, int]:
    """Applique les motifs ligne à ligne. Retourne (lignes de bibliothèque embarquée sautées, erreurs trouvées)."""
    sautees = erreurs = 0
    for p in ctx.fichiers_code(extensions):
        for numero, ligne in enumerate((ctx.texte(p) or '').splitlines(), 1):
            if len(ligne) > LIGNE_MINIFIEE:
                sautees += 1
                continue
            if 'nosec' in ligne:
                continue
            for motif, message, bloquant in motifs:
                if motif.search(ligne):
                    erreurs += bloquant
                    (ctx.bilan.erreur if bloquant else ctx.bilan.alerte)(
                        f'Code — {ctx.rel(p)}:{numero} : {message} (si c\'est justifié : « nosec : raison » sur la ligne)')
    return sautees, erreurs


def compter(ctx: Contexte, motif: re.Pattern) -> dict[str, int]:
    """Nombre d'occurrences d'un motif par fichier web, hors bibliothèques embarquées et module de prise en main."""
    comptes: dict[str, int] = {}
    for p in ctx.fichiers_code(EXT_WEB):
        if p.name in MODULE_PRISE_EN_MAIN:
            continue
        nombre = sum(1 for ligne in (ctx.texte(p) or '').splitlines()
                     if len(ligne) <= LIGNE_MINIFIEE and 'nosec' not in ligne and motif.search(ligne))
        if nombre:
            comptes[ctx.rel(p)] = nombre
    return comptes


def motifs_dangereux(ctx: Contexte) -> None:
    sautees_py, erreurs_py = chercher_motifs(ctx, EXT_PYTHON, MOTIFS_PYTHON)
    sautees_web, erreurs_web = chercher_motifs(ctx, EXT_WEB, MOTIFS_WEB)
    if not erreurs_py and not erreurs_web:
        ctx.bilan.reussi('Aucun motif dangereux dans le code (eval, shell=True, SQL construit, document.write…)')
    dynamique = compter(ctx, RE_HTML_DYNAMIQUE)
    if dynamique:
        detail = ', '.join(f'{f} ({n})' for f, n in dynamique.items())
        ctx.bilan.alerte(f'HTML inséré par le code (innerHTML…) : {detail}. Vérifier qu\'aucune donnée importée ou saisie '
                         'n\'y passe telle quelle (sinon textContent), puis marquer les lignes sûres « nosec : texte fixe »')
    stockage = compter(ctx, RE_STOCKAGE)
    if stockage:
        ctx.bilan.alerte('Stockage du navigateur utilisé (' + ', '.join(stockage) + ') : aucune donnée de personne ne doit y rester')
        if not fichiers_qui_contiennent(ctx, re.compile(r'(?i)\bexport|sauvegarder|t[ée]l[ée]charger')):
            ctx.bilan.alerte('Les saisies sont gardées dans le navigateur, sans fonction d\'export : elles disparaissent si l\'agent change de poste '
                             'ou vide son navigateur. Prévoir « Exporter » et « Importer » (fichier JSON)')
    if sautees_py + sautees_web:
        ctx.bilan.non_teste(f'{sautees_py + sautees_web} ligne(s) de bibliothèque embarquée (très longues) non analysées : '
                            'elles relèvent de docs/composants.md')


RE_SCRIPT_INTERNE = re.compile(r'(?is)<script\b([^>]*)>(.*?)</script>')


def scripts_internes(html: str) -> list[tuple[str, str]]:
    """Les blocs <script> écrits dans la page : (extension à utiliser, code)."""
    blocs = []
    for attributs, code in RE_SCRIPT_INTERNE.findall(html):
        genre = re.search(r'\btype\s*=\s*["\']?([^"\'\s>]+)', attributs)
        nature = genre.group(1).lower() if genre else 'text/javascript'
        if re.search(r'\bsrc\s*=', attributs) or not code.strip():
            continue
        if nature == 'module':
            blocs.append(('.mjs', code))
        elif nature in ('text/javascript', 'application/javascript'):
            blocs.append(('.js', code))
    return blocs


def verifier_js(ctx: Contexte, source: str, extension: str, origine: str, temporaire: Chemin) -> bool:
    fichier = temporaire / f'bloc{extension}'
    fichier.write_text(source, encoding='utf-8')
    code, sortie = lancer(['node', '--check', str(fichier)], ctx.racine, 60)
    if code != 0 and extension == '.js' and re.search(r'(?m)^\s*(?:import|export)\s', source):
        fichier = temporaire / 'bloc.mjs'                     # module écrit dans un fichier .js
        fichier.write_text(source, encoding='utf-8')
        code, sortie = lancer(['node', '--check', str(fichier)], ctx.racine, 60)
    if code == 0:
        return True
    ctx.bilan.erreur(f'Erreur de syntaxe JavaScript — {origine} : {fin_de_sortie(sortie, 4, 300)}')
    return False


def syntaxe_javascript(ctx: Contexte) -> None:
    fichiers = ctx.fichiers(extensions={'.js', '.mjs', '.cjs', '.html', '.htm'})
    if not fichiers:
        return
    if not shutil.which('node'):
        ctx.outil_absent('node', 'contrôle de la syntaxe JavaScript')
        return
    verifies, justes = 0, True
    with tempfile.TemporaryDirectory() as dossier:
        for p in fichiers:
            texte = ctx.texte(p) or ''
            if p.suffix.lower() in ('.html', '.htm'):
                blocs = [(ext, code, f'{ctx.rel(p)}, bloc <script> n° {i}') for i, (ext, code) in enumerate(scripts_internes(texte), 1)]
            else:
                blocs = [(p.suffix.lower(), texte, ctx.rel(p))]
            for extension, source, origine in blocs:
                verifies += 1
                justes = verifier_js(ctx, source, extension, origine, Chemin(dossier)) and justes
    if verifies and justes:
        ctx.bilan.reussi(f'JavaScript : syntaxe correcte ({verifies} fichier(s) ou bloc(s) <script>)')


def controle_code(ctx: Contexte) -> None:
    analyse_python(ctx)
    syntaxe_javascript(ctx)
    motifs_dangereux(ctx)


# ================================================================ 6. secrets
RE_SECRET_QUOTE = re.compile(r'(?i)(password|passwd|mot_de_passe|motdepasse|secret|token|api[_-]?key|apikey)'
                             r'["\']?\s*[:=]\s*["\']([^"\'\s]{6,})["\']')
RE_SECRET_BRUT = re.compile(r'(?im)^\s*[A-Z0-9_]*(PASSWORD|PASSWD|MOT_DE_PASSE|MOTDEPASSE|SECRET|TOKEN|API_?KEY)[A-Z0-9_]*'
                            r'\s*[:=]\s*([^\s#"\'$<{][^\s#]*)')
RE_JETONS = [re.compile(p) for p in (r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----', r'AKIA[0-9A-Z]{16}',
                                      r'\bsk-[A-Za-z0-9]{20,}', r'\bghp_[A-Za-z0-9]{30,}', r'\bxox[bp]-[A-Za-z0-9-]{10,}')]
FACTICE = re.compile(r'(?i)(changeme|exemple|example|xxx+|\*{3,}|fictif|motdepasse|votre|your|placeholder|todo|à[-_ ]?compléter)')
VALEUR_INDIRECTE = ('${', '{{', '$(', '%', 'os.', 'process.')
EXT_VALEUR_BRUTE = {'.yaml', '.yml', '.ini', '.conf', '.cfg', '.toml', '.env', '.exemple', '.sh', '.ps1'}


def secret_dans_ligne(ligne: str, valeur_brute: bool, documentation: bool) -> str | None:
    """Nature du secret repéré dans la ligne, ou None."""
    if 'nosecret' in ligne:
        return None
    if any(jeton.search(ligne) for jeton in RE_JETONS):
        return 'jeton ou clé privée'
    if documentation:
        return None
    candidats = [RE_SECRET_QUOTE.search(ligne)] + ([RE_SECRET_BRUT.search(ligne)] if valeur_brute else [])
    for m in candidats:
        if m and not FACTICE.search(m.group(2)) and not m.group(2).startswith(VALEUR_INDIRECTE):
            return f'« {m.group(1)} » écrit en dur'
    return None


def fichiers_env_reels(ctx: Contexte) -> list[str]:
    reels = []
    for p in ctx.racine.rglob('*'):
        ignore = any(part in DOSSIERS_IGNORES for part in p.relative_to(ctx.racine).parts)
        est_env = p.name == '.env' or p.name.startswith('.env.') or p.suffix == '.env'
        if p.is_file() and est_env and not ignore and p.name not in FICHIERS_ENV_AUTORISES:
            reels.append(ctx.rel(p))
    return reels


def analyse_gitleaks(ctx: Contexte) -> None:
    if not shutil.which('gitleaks'):
        ctx.outil_absent('gitleaks', 'recherche approfondie de secrets (seule l\'analyse intégrée, plus simple, a été faite)')
        return
    code, _ = lancer(['gitleaks', 'detect', '--no-git', '--source', str(ctx.racine), '--redact', '--no-banner'], ctx.racine, 180)
    if code == 0:
        ctx.bilan.reussi('gitleaks : aucun secret trouvé')
    elif code == 1:
        ctx.bilan.erreur('gitleaks a trouvé des secrets (lancer « gitleaks detect --no-git --source . » pour le détail)')
    else:
        ctx.bilan.alerte('gitleaks n\'a pas pu s\'exécuter correctement : analyse à refaire')


def controle_secrets(ctx: Contexte) -> None:
    trouves = set()
    for p in ctx.fichiers():
        suffixe = p.suffix.lower()
        valeur_brute = suffixe in EXT_VALEUR_BRUTE or p.name.startswith('.env')
        for numero, ligne in enumerate((ctx.texte(p) or '').splitlines(), 1):
            nature = secret_dans_ligne(ligne, valeur_brute, suffixe == '.md') if len(ligne) <= LIGNE_MINIFIEE else None
            if nature:
                trouves.add(f'{ctx.rel(p)}:{numero} ({nature})')
    for fichier in fichiers_env_reels(ctx):
        trouves.add(f'{fichier} (fichier .env réel : à ne jamais laisser dans le dossier de travail)')
    for trouve in sorted(trouves):
        ctx.bilan.erreur('Secret possible — ' + trouve + ' (si c\'est un exemple fictif, ajouter « nosecret » sur la ligne)')
    if not trouves:
        ctx.bilan.reussi('Aucun secret en dur repéré (contrôle intégré)')
    if not re.search(r'(?m)^\.env\s*$', ctx.texte(ctx.racine / '.gitignore') or ''):
        ctx.bilan.erreur('.gitignore doit exclure « .env »')
    analyse_gitleaks(ctx)


# ================================================================ 7. réseau sortant
RE_RESSOURCES = [
    re.compile(r'(?is)<script\b[^>]*\bsrc\s*=\s*["\'](?:https?:)?//([^/"\'?#:]+)'),
    re.compile(r'(?is)<link\b[^>]*\bhref\s*=\s*["\'](?:https?:)?//([^/"\'?#:]+)'),
    re.compile(r'(?is)<(?:img|source|iframe|video|audio|embed|object)\b[^>]*\b(?:src|data)\s*=\s*["\'](?:https?:)?//([^/"\'?#:]+)'),
    re.compile(r'(?i)@import\s+(?:url\()?["\']?(?:https?:)?//([^/"\')?#:]+)'),
    re.compile(r'(?i)\burl\(\s*["\']?(?:https?:)?//([^/"\')?#:]+)'),
    re.compile(r'(?i)\bfetch\(\s*["\'`](?:https?:)?//([^/"\'`?#:]+)'),
    re.compile(r'(?i)\.open\(\s*["\'][A-Z]+["\']\s*,\s*["\'`](?:https?:)?//([^/"\'`?#:]+)'),
    re.compile(r'(?i)new\s+(?:WebSocket|EventSource)\(\s*["\'`](?:wss?|https?)://([^/"\'`?#:]+)'),
    re.compile(r'(?i)\bimport\b[^;\n]*\bfrom\s*["\']https?://([^/"\'?#:]+)'),
    re.compile(r'(?i)(?:requests\.(?:get|post|put|delete|request|head)|urlopen|httpx\.\w+|axios(?:\.\w+)?|curl\s+-\S*)'
               r'\s*\(?\s*["\']?https?://([^/"\'\s?#:]+)'),
]
HOTES_TOLERES = {'localhost', '127.0.0.1', '::1', 'www.w3.org'}   # espaces de noms XML/SVG : pas un appel réseau


def hotes_autorises(ctx: Contexte) -> set[str]:
    """Hôtes déclarés dans reseau-autorise.txt ; un hôte sans raison écrite est refusé."""
    autorises = set()
    for ligne in (ctx.texte(ctx.racine / 'reseau-autorise.txt') or '').splitlines():
        mots = ligne.split('#', 1)[0].split()
        if not mots:
            continue
        autorises.add(mots[0].lower())
        if len(mots) < 2:
            ctx.bilan.erreur(f'reseau-autorise.txt : l\'hôte « {mots[0]} » est déclaré sans raison (écrire la raison après le nom)')
    return autorises


def controle_reseau(ctx: Contexte) -> None:
    autorises = hotes_autorises(ctx)
    hors: dict[str, set[str]] = {}
    for p in ctx.fichiers(extensions={'.py', '.js', '.mjs', '.ts', '.html', '.htm', '.css', '.sh', '.ps1', '.vue'}):
        texte = ctx.texte(p) or ''
        for motif in RE_RESSOURCES:
            for m in motif.finditer(texte):
                hote = m.group(1).lower()
                if hote not in HOTES_TOLERES and hote not in autorises:
                    hors.setdefault(hote, set()).add(ctx.rel(p))
    for hote, sources in sorted(hors.items()):
        rappel = ' — règle absolue : aucun appel à l\'API Anthropic' if 'anthropic' in hote else ''
        ctx.bilan.erreur(f'Appel réseau non déclaré vers « {hote} » dans {", ".join(sorted(sources)[:3])}{rappel}. '
                         'Soit on le supprime (bibliothèque embarquée), soit on l\'ajoute à reseau-autorise.txt avec sa raison')
    if not hors:
        declares = f' ({len(autorises)} hôte(s) déclaré(s))' if autorises else ''
        ctx.bilan.reussi('Aucun appel réseau sortant hors liste déclarée' + declares)
    ctx.bilan.non_teste('Le contrôle réseau lit le code ; le test navigateur (test_prise_en_main.py, ou Playwright) vérifie l\'exécution réelle')


# ================================================================ 8. dépendances figées
def controle_requirements(ctx: Contexte) -> list[Chemin]:
    fichiers = [p for p in ctx.fichiers(extensions={'.txt'}) if re.fullmatch(r'requirements[\w.-]*\.txt', p.name)]
    for p in fichiers:
        lignes = [ligne.split('#', 1)[0].strip() for ligne in (ctx.texte(p) or '').splitlines()]
        paquets = [ligne for ligne in lignes if ligne and not ligne.startswith(('-', '--'))]
        libres = [ligne for ligne in paquets if '==' not in ligne and ' @ ' not in ligne]
        if libres:
            ctx.exiger(f'Dépendances non figées — {ctx.rel(p)} : {", ".join(libres[:5])} (écrire paquet==version)')
        elif paquets:
            ctx.bilan.reussi(f'{ctx.rel(p)} : {len(paquets)} dépendance(s), toutes figées')
        if paquets and '--hash=' not in (ctx.texte(p) or ''):
            ctx.bilan.alerte(f'{ctx.rel(p)} : pas d\'empreintes (--hash) ; les ajouter protège contre un paquet remplacé')
    return fichiers


def controle_package_json(ctx: Contexte) -> list[Chemin]:
    verrous = []
    for p in ctx.fichiers(extensions={'.json'}):
        if p.name != 'package.json':
            continue
        try:
            contenu = json.loads(ctx.texte(p) or '{}')
        except json.JSONDecodeError:
            ctx.bilan.erreur(f'{ctx.rel(p)} : fichier JSON illisible')
            continue
        verrou = p.with_name('package-lock.json')
        if (contenu.get('dependencies') or contenu.get('devDependencies')) and not verrou.exists():
            ctx.exiger(f'Dépendances non figées — {ctx.rel(p)} sans package-lock.json (lancer npm install puis livrer le verrou)')
        elif verrou.exists():
            verrous.append(verrou)
    return verrous


RE_FROM = re.compile(r'(?im)^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)')


def controle_dockerfiles(ctx: Contexte) -> None:
    for p in sorted(ctx.racine.rglob('Dockerfile')) + sorted(ctx.racine.rglob('*.Dockerfile')):
        if any(part in DOSSIERS_IGNORES for part in p.relative_to(ctx.racine).parts):
            continue
        texte = ctx.texte(p) or ''
        fautes = []
        etapes = {nom.lower() for nom in re.findall(r'(?im)^\s*FROM\s+\S+\s+AS\s+(\S+)', texte)} | {'scratch'}
        for image in RE_FROM.findall(texte):
            precise = '@sha256:' in image or (':' in image.split('/')[-1] and not image.endswith(':latest'))
            if image.lower() not in etapes and not precise:
                fautes.append(f'image de base « {image} » sans version précise')
        if re.search(r'(?im)^\s*ADD\s+https?://', texte):
            fautes.append('ADD depuis une adresse Internet (télécharger, vérifier l\'empreinte, puis COPY)')
        if re.search(r'(?m)^\s*(?:ENV|ARG)\s+(?:\w+_)?(?:PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|KEY)(?:_\w+)?[= ]\s*[^\s$]', texte):
            fautes.append('secret écrit dans le Dockerfile')
        for faute in fautes:
            ctx.bilan.erreur(f'Dockerfile — {ctx.rel(p)} : {faute}')
        utilisateurs = re.findall(r'(?im)^\s*USER\s+(\S+)', texte)
        if (not utilisateurs or utilisateurs[-1] in ('root', '0')) and not ctx.derogation_notee('non root', 'user'):
            ctx.bilan.alerte(f'Dockerfile — {ctx.rel(p)} : l\'application tourne en root (ajouter USER, ou noter l\'exception)')
        if not fautes:
            ctx.bilan.reussi(f'{ctx.rel(p)} : image de base figée, aucun secret')


def controle_dependances(ctx: Contexte) -> tuple[list[Chemin], list[Chemin]]:
    requirements = controle_requirements(ctx)
    verrous = controle_package_json(ctx)
    controle_dockerfiles(ctx)
    return requirements, verrous


# ================================================================ 9. analyses avec les outils installés
PANNE_RESEAU = re.compile(r'(?i)ENOTFOUND|ECONNREFUSED|EAI_AGAIN|ETIMEDOUT|ConnectionError|Max retries|Name or service not known|'
                          r'Temporary failure|network|proxy')


def analyse_ruff(ctx: Contexte) -> None:
    if not shutil.which('ruff'):
        ctx.outil_absent('ruff', 'analyse du code Python (noms inconnus, imports inutiles, pièges courants)')
        return
    cibles = [d for d in [*emplacements_code(ctx), 'tests', 'deploy'] if (ctx.racine / d).exists()]
    base = ['ruff', 'check', '--no-cache', '--output-format', 'concise', '--exclude', 'build', *cibles]
    code, sortie = lancer([*base, '--select', 'E9,F'], ctx.racine, 120)
    if code == 0:
        ctx.bilan.reussi('ruff : aucune erreur (noms inconnus, imports inutiles, syntaxe)')
    elif code == 1:
        ctx.bilan.erreur(f'ruff — erreurs à corriger : {fin_de_sortie(sortie, 10)}')
    else:
        ctx.bilan.alerte(f'ruff n\'a pas pu tourner : {fin_de_sortie(sortie, 2, 200)}')
    code, sortie = lancer([*base, '--select', 'B,C901,SIM', '--exit-zero', '--statistics'], ctx.racine, 120)
    conseils = [ligne.strip() for ligne in sortie.splitlines() if re.match(r'^\s*\d+\s+[A-Z]+\d+', ligne)]
    if code == 0 and conseils:
        ctx.bilan.alerte('ruff — conseils de relecture (pièges, complexité, simplifications) : ' + ' ; '.join(conseils[:6]))


def analyse_bandit(ctx: Contexte) -> None:
    cibles = [d for d in emplacements_code(ctx) if (ctx.racine / d).is_dir() or d.endswith('.py')]
    cibles = [d for d in cibles if (ctx.racine / d).exists()]
    if not cibles:
        return
    if not shutil.which('bandit'):
        ctx.outil_absent('bandit', 'analyse de sécurité du code Python')
        return
    code, sortie = lancer(['bandit', '-q', '-r', *cibles, '-ll'], ctx.racine, 180)
    if code == 0:
        ctx.bilan.reussi('bandit : aucun défaut de sécurité de gravité moyenne ou haute')
    elif code == 1:
        issues = [ligne.strip() for ligne in sortie.splitlines() if ligne.strip().startswith(('>> Issue', 'Location'))]
        ctx.bilan.erreur('bandit — défauts de sécurité : ' + ' ⏎ '.join(issues[:8]))
    else:
        ctx.bilan.alerte(f'bandit n\'a pas pu tourner : {fin_de_sortie(sortie, 2, 200)}')


def analyse_pip_audit(ctx: Contexte, requirements: list[Chemin]) -> None:
    if not requirements:
        return
    if not shutil.which('pip-audit'):
        ctx.outil_absent('pip-audit', 'recherche de failles connues dans les dépendances Python')
        return
    for p in requirements:
        code, sortie = lancer(['pip-audit', '-r', str(p), '--no-deps', '--disable-pip', '--progress-spinner', 'off'], ctx.racine, 240)
        if code == 0:
            ctx.bilan.reussi(f'pip-audit : aucune faille connue dans {ctx.rel(p)}')
        elif code is not None and re.search(r'(?i)found \d+ known vulnerabilit', sortie):
            utile = '\n'.join(ligne for ligne in sortie.splitlines() if not ligne.startswith('WARNING'))
            ctx.bilan.erreur(f'pip-audit — failles connues dans {ctx.rel(p)} : {fin_de_sortie(utile, 6)}')
        else:
            ctx.bilan.non_teste(f'pip-audit n\'a pas pu interroger la base des failles pour {ctx.rel(p)} ({fin_de_sortie(sortie, 1, 160)})')


def analyse_npm_audit(ctx: Contexte, verrous: list[Chemin]) -> None:
    if not verrous:
        return
    if not shutil.which('npm'):
        ctx.outil_absent('npm', 'recherche de failles connues dans les dépendances JavaScript')
        return
    for verrou in verrous:
        code, sortie = lancer(['npm', 'audit', '--omit=dev', '--audit-level=high'], verrou.parent, 240)
        if code == 0:
            ctx.bilan.reussi(f'npm audit : aucune faille haute ou critique ({ctx.rel(verrou)})')
        elif code is not None and 'vulnerabilit' in sortie.lower() and not PANNE_RESEAU.search(sortie):
            ctx.bilan.erreur(f'npm audit — failles hautes ou critiques ({ctx.rel(verrou)}) : {fin_de_sortie(sortie, 5)}')
        else:
            ctx.bilan.non_teste(f'npm audit n\'a pas pu interroger la base des failles ({ctx.rel(verrou)})')


def analyse_trivy(ctx: Contexte) -> None:
    if ctx.format != 'B' or not ctx.images:
        return
    if not ctx.analyser_images:
        ctx.bilan.non_teste('Images non analysées (lancer avec --analyser-images sur une machine qui a trivy et l\'accès au registre)')
        return
    if not shutil.which('trivy'):
        ctx.outil_absent('trivy', 'recherche de failles dans les images')
        return
    for image in ctx.images:
        code, sortie = lancer(['trivy', 'image', '--quiet', '--severity', 'HIGH,CRITICAL', '--exit-code', '1', image], ctx.racine, 900)
        if code == 0:
            ctx.bilan.reussi(f'trivy : aucune faille haute ou critique dans {image}')
        elif code == 1:
            ctx.bilan.erreur(f'trivy — failles hautes ou critiques dans {image} : {fin_de_sortie(sortie, 6)}')
        else:
            ctx.bilan.non_teste(f'trivy n\'a pas pu analyser {image} ({fin_de_sortie(sortie, 1, 160)})')


def controle_analyses(ctx: Contexte, requirements: list[Chemin], verrous: list[Chemin]) -> None:
    if ctx.fichiers(extensions=EXT_PYTHON):
        analyse_ruff(ctx)
        analyse_bandit(ctx)
    analyse_pip_audit(ctx, requirements)
    analyse_npm_audit(ctx, verrous)
    analyse_trivy(ctx)


# ================================================================ 10. compose, vhost, restauration (format B)
RE_SECRET_COMPOSE = re.compile(r'^\s+(?:-\s*)?["\']?([A-Za-z0-9_]*(?:PASSWORD|PASSWD|MOT_DE_PASSE|SECRET|TOKEN|KEY)[A-Za-z0-9_]*)'
                               r'["\']?\s*[:=]\s*["\']?([^\s"\'#]+)')
DURCISSEMENTS = (('read_only', r'(?m)^\s+read_only:\s*true'), ('cap_drop', r'(?m)^\s+cap_drop:'),
                 ('no-new-privileges', r'no-new-privileges'))


def blocs_services(lignes: list[str]) -> dict[str, list[str]]:
    """Découpe le compose en services, quelle que soit la largeur de l'indentation."""
    services: dict[str, list[str]] = {}
    dans, courant, retrait = False, None, None
    for ligne in lignes:
        if re.match(r'^services:\s*(#.*)?$', ligne):
            dans = True
            continue
        if not dans or not ligne.strip() or ligne.lstrip().startswith('#'):
            continue
        if not ligne.startswith(' '):
            dans = False
            continue
        espaces = len(ligne) - len(ligne.lstrip(' '))
        retrait = espaces if retrait is None else retrait
        m = re.match(r'^\s+([A-Za-z0-9_.-]+):\s*(#.*)?$', ligne)
        if espaces == retrait and m:
            courant = m.group(1)
            services[courant] = []
        elif courant is not None:
            services[courant].append(ligne)
    return services


def ports_ouverts(bloc: list[str]) -> list[str]:
    ouverts, dans_ports = [], False
    for ligne in bloc:
        if re.match(r'^\s+ports:\s*(#.*)?$', ligne):
            dans_ports = True
            continue
        if not dans_ports:
            continue
        m = re.match(r'^\s+-\s*["\']?([^"\'\s#]+)["\']?\s*(#.*)?$', ligne)
        if m and not m.group(1).startswith('127.0.0.1:'):
            ouverts.append(m.group(1))
        elif not m and ligne.strip() and not ligne.strip().startswith('#'):
            dans_ports = False
    return ouverts


def fautes_service(ctx: Contexte, nom: str, bloc: list[str]) -> list[str]:
    """Écarts bloquants d'un service du compose."""
    texte = '\n'.join(bloc)
    fautes = []
    image = re.search(r'(?m)^\s+image:\s*["\']?([^\s"\'#]+)', texte)
    if image:
        reference = image.group(1)
        ctx.images.append(reference)
        if '@sha256:' not in reference and (':' not in reference.split('/')[-1] or reference.endswith(':latest')):
            fautes.append(f'{nom} : image « {reference} » sans version précise (ni « latest », ni absence de version)')
    elif not re.search(r'(?m)^\s+build:', texte):
        fautes.append(f'{nom} : ni image ni build')
    if not re.search(r'(?m)^\s+restart:\s*["\']?always["\']?\s*(#.*)?$', texte):
        fautes.append(f'{nom} : « restart: always » manquant (seule valeur relancée après un redémarrage de la VM)')
    if re.search(r'(?m)^\s+privileged:\s*true', texte) or re.search(r'(?m)^\s+network_mode:\s*["\']?host', texte):
        fautes.append(f'{nom} : « privileged » ou « network_mode: host » interdits')
    fautes += [f'{nom} : port « {port} » publié sur toutes les interfaces (écrire 127.0.0.1:port:port)' for port in ports_ouverts(bloc)]
    for ligne in bloc:
        m = RE_SECRET_COMPOSE.match(ligne)
        if m and not m.group(2).startswith(('${', '$(', '{{')) and not FACTICE.search(m.group(2)):
            fautes.append(f'{nom} : « {m.group(1)} » écrit en clair dans le compose (le mettre dans .env)')
    return fautes


def conseils_service(ctx: Contexte, nom: str, bloc: list[str]) -> None:
    """Durcissements attendus par défaut : absents, ils demandent une exception notée."""
    texte = '\n'.join(bloc)
    if not re.search(r'(?m)^\s+healthcheck:', texte):
        ctx.bilan.alerte(f'{nom} : pas de healthcheck')
    if not re.search(r'(?m)^\s+(mem_limit|mem_reservation):|resources:', texte):
        ctx.bilan.alerte(f'{nom} : pas de limite mémoire')
    for mot, motif in DURCISSEMENTS:
        if not re.search(motif, texte) and not ctx.derogation_notee(mot):
            ctx.bilan.alerte(f'{nom} : « {mot} » absent et aucune exception notée dans docs/derogations.md')
    if not re.search(r'(?m)^\s+user:', texte) and not ctx.derogation_notee('non root', 'user'):
        ctx.bilan.alerte(f'{nom} : pas d\'utilisateur non root et aucune exception notée')


def controle_compose(ctx: Contexte) -> None:
    noms = ('compose.yaml', 'compose.yml', 'docker-compose.yml', 'docker-compose.yaml')
    compose = next((ctx.racine / 'deploy' / n for n in noms if (ctx.racine / 'deploy' / n).exists()), None)
    if compose is None:
        ctx.bilan.erreur('Format B : deploy/compose.yaml absent')
        return
    lignes = (ctx.texte(compose) or '').splitlines()
    services = blocs_services(lignes)
    if not services:
        ctx.bilan.erreur('deploy/compose.yaml : aucun service reconnu')
        return
    fautes = [faute for nom, bloc in services.items() for faute in fautes_service(ctx, nom, bloc)]
    for nom, bloc in services.items():
        conseils_service(ctx, nom, bloc)
    if re.search(r'env_file|\$\{', '\n'.join(lignes)) and not (ctx.racine / 'deploy' / '.env.exemple').exists():
        fautes.append('le compose utilise un fichier d\'environnement mais deploy/.env.exemple est absent')
    for faute in fautes:
        ctx.bilan.erreur('Compose — ' + faute)
    if not fautes:
        ctx.bilan.reussi(f'Compose conforme au socle ({len(services)} service(s))')


def controle_vhost(ctx: Contexte) -> None:
    vhosts = sorted((ctx.racine / 'deploy').glob('*.conf'))
    if not vhosts:
        ctx.bilan.erreur('Format B : aucun vhost nginx (deploy/<nom>.conf)')
    for vhost in vhosts:
        texte = ctx.texte(vhost) or ''
        if not re.search(r'proxy_pass\s+http://127\.0\.0\.1:\d+', texte):
            ctx.bilan.erreur(f'{vhost.name} : proxy_pass doit viser http://127.0.0.1:<port>')
        if not re.search(r'(?m)^\s*deny\s+all\s*;', texte) and not ctx.derogation_notee('ouverture externe', 'accès externe'):
            ctx.bilan.erreur(f'{vhost.name} : pas de « deny all » (réseau interne). Une ouverture externe est une décision écrite : '
                             'noter « ouverture externe » dans docs/derogations.md et lire references/ouverture-externe.md')
        for entete in ('X-Content-Type-Options', 'Strict-Transport-Security', 'Content-Security-Policy'):
            if entete not in texte:
                ctx.bilan.alerte(f'{vhost.name} : en-tête {entete} absent')
        if 'client_max_body_size' not in texte:
            ctx.bilan.alerte(f'{vhost.name} : taille maximale des dépôts (client_max_body_size) non fixée')


def controle_restauration(ctx: Contexte) -> None:
    valeur = champ_fiche(ctx.texte(ctx.racine / 'docs' / 'fiche-dsi.md') or '', 'Dernier essai de restauration')
    date = lire_date(valeur or '')
    if date is None:
        ctx.bilan.alerte('Sauvegarde : aucun essai de restauration daté dans docs/fiche-dsi.md — à faire sur le serveur de test '
                         'avant la mise en production (une sauvegarde jamais restaurée n\'est pas une sauvegarde)')
    elif date < ctx.aujourdhui - datetime.timedelta(days=365):
        ctx.bilan.alerte(f'Sauvegarde : dernier essai de restauration il y a plus d\'un an ({date.isoformat()}) — à refaire')
    else:
        ctx.bilan.reussi(f'Sauvegarde : restauration essayée le {date.isoformat()}')


def controle_integration(ctx: Contexte) -> None:
    controle_compose(ctx)
    controle_vhost(ctx)
    controle_restauration(ctx)


# ================================================================ 11. composants
def etat_composant(ctx: Contexte, cases: list[str]) -> tuple[str | None, str | None]:
    """(faute bloquante, alerte) pour une ligne de docs/composants.md."""
    nom, fin = cases[0], cases[3]
    if not fin:
        return f'{nom} : date de fin de support non renseignée', None
    date = lire_date(fin)
    if date is None:
        sans_date = 'sans date' in fin.lower() or 'maintenu' in fin.lower()
        if sans_date and len(cases) >= 5 and cases[4]:
            return None, None
        return (f'{nom} : « {fin} » sans source indiquée' if sans_date
                else f'{nom} : date « {fin} » illisible (écrire AAAA-MM ou AAAA-MM-JJ)'), None
    if date < ctx.aujourdhui:
        return f'{nom} : support terminé depuis le {date.isoformat()}', None
    if date < ctx.aujourdhui + datetime.timedelta(days=183):
        return None, f'{nom} (fin de support {date.isoformat()})'
    return None, None


def controle_composants(ctx: Contexte) -> None:
    texte = ctx.texte(ctx.racine / 'docs' / 'composants.md') or ''
    lignes = [cases for cases in lignes_tableau(texte) if len(cases) >= 4]
    if not lignes:
        ctx.exiger('docs/composants.md : aucun composant listé (bibliothèques embarquées comprises, avec leur version)')
        return
    renseignees = [cases for cases in lignes if not RE_MARQUEUR.search(' '.join(cases))]
    if not renseignees:
        ctx.bilan.alerte('docs/composants.md : composants pas encore renseignés')
        return
    etats = [etat_composant(ctx, cases) for cases in renseignees]
    fautes = [faute for faute, _ in etats if faute]
    for faute in fautes:
        ctx.bilan.erreur('Composant — ' + faute)
    for _, alerte in etats:
        if alerte:
            ctx.bilan.alerte('Composant bientôt sans support (moins de 6 mois) — ' + alerte)
    for image in ctx.images:
        nom_image = re.sub(r'[:@].*$', '', image).split('/')[-1].lower()
        if nom_image and nom_image not in texte.lower():
            ctx.exiger(f'Composant — l\'image « {image} » du compose n\'est pas listée dans docs/composants.md')
    if not fautes:
        ctx.bilan.reussi(f'{len(lignes)} composant(s) listé(s), supports en cours')


# ================================================================ 12. exceptions, périmètre, décisions
def suivi_exceptions(ctx: Contexte) -> None:
    for cases in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'derogations.md') or ''):
        if len(cases) < 6 or not cases[0] or RE_MARQUEUR.search(' '.join(cases)):
            continue
        date = lire_date(cases[5])
        if date is None:
            ctx.bilan.alerte(f'Exception « {cases[0]} » : date de revue absente ou illisible')
        elif date < ctx.aujourdhui:
            ctx.bilan.alerte(f'Exception « {cases[0]} » : date de revue dépassée ({date.isoformat()}) — à revoir ou à fermer')
        else:
            ctx.bilan.alerte(f'Exception ouverte à signaler à la livraison : « {cases[0]} » (revue avant le {date.isoformat()})')


def suivi_perimetre_et_incidents(ctx: Contexte) -> None:
    for cases in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'perimetre.md') or ''):
        if len(cases) >= 3 and cases[1] and cases[2].lower().startswith('non'):
            ctx.bilan.alerte(f'Changement de périmètre pas encore dans la SPEC : « {cases[1]} » — à faire valider par la cellule')
    for cases in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'incidents.md') or ''):
        if len(cases) >= 2 and cases[-1].lower().startswith('ouvert'):
            ctx.bilan.alerte(f'Incident encore ouvert ({cases[0]}) : {cases[2] if len(cases) > 2 else "voir docs/incidents.md"}')


def suivi_decisions(ctx: Contexte) -> None:
    if ctx.niveau == NIVEAU_PARTAGE:
        return                                       # le journal des décisions est demandé à partir du niveau durable
    decisions = ctx.texte(ctx.racine / 'docs' / 'decisions.md')
    if decisions is None:
        ctx.bilan.alerte('docs/decisions.md absent : noter en trois lignes les choix techniques (format, bibliothèques) et leur raison')
    elif not [cases for cases in lignes_tableau(decisions) if cases and cases[0] and not RE_MARQUEUR.search(' '.join(cases))]:
        ctx.bilan.alerte('docs/decisions.md : aucune décision technique notée (au moins le choix du format et sa raison)')


def controle_suivi(ctx: Contexte) -> None:
    suivi_exceptions(ctx)
    suivi_perimetre_et_incidents(ctx)
    suivi_decisions(ctx)


# ================================================================ 13. partage et transmission
def signaler_partage(ctx: Contexte, cellule: str) -> None:
    """Outil réutilisable : la cellule opérationnelle est-elle au courant ? Alerte amicale, jamais bloquante."""
    if a_completer(cellule):
        ctx.bilan.alerte('Cet outil pourrait servir à d\'autres et la cellule opérationnelle n\'en est pas informée : '
                         'un outil caché dans une licence, c\'est un vélo électrique dans un garage. '
                         'Faites-le connaître à la cellule ou dans l\'intranet (la skill propose de rédiger le message).')
    elif cellule.lower().startswith('non'):
        ctx.bilan.reussi('Partage : potentiel de réutilisation déclaré, diffusion non souhaitée pour l\'instant (raison notée)')
    else:
        ctx.bilan.reussi(f'Partage : la cellule opérationnelle a été informée ({cellule})')


def controle_partage(ctx: Contexte) -> None:
    texte = ctx.texte(ctx.racine / 'docs' / 'partage.md')
    if texte is None:
        ctx.bilan.alerte('docs/partage.md absent : fiche de partage et de transmission à créer (voir references/partage-et-transmission.md)')
        return
    potentiel = (champ_fiche(texte, 'Potentiel de réutilisation') or '').lower()
    cellule = champ_fiche(texte, 'Cellule opérationnelle informée') or ''
    if a_completer(potentiel):
        return                                       # déjà signalé par le contrôle des champs à compléter
    if potentiel.startswith('non'):
        ctx.bilan.reussi('Partage : pas de potentiel de réutilisation déclaré')
    elif potentiel.startswith(('oui', 'peut')):
        signaler_partage(ctx, cellule)
    installation = (champ_fiche(texte, 'Demande d\'installation') or '').lower()
    if installation.startswith('oui') and ctx.niveau == NIVEAU_PARTAGE:
        ctx.bilan.alerte('Vous souhaitez une installation par la cellule : le niveau durable est nécessaire. '
                         'Rien n\'est perdu, la skill reprend ce qui existe et complète le dossier avec vous.')
    if champ_fiche(texte, 'Exercice de reprise') == '':
        ctx.bilan.alerte('Transmission : aucun exercice de reprise noté (le suppléant rejoue la mise à jour avec la seule documentation)')


# ================================================================ 15. données réelles de personnes
RE_NIR = re.compile(r'(?<![\dA-Za-z])([12])\s?(\d{2})\s?(0[1-9]|1[0-2]|[2-9]\d)\s?(\d{2}|2[AB])\s?(\d{3})\s?(\d{3})\s?(\d{2})(?![\dA-Za-z])')
RE_IBAN_FR = re.compile(r'(?<![0-9A-Za-z])FR\d{2}(?:\s?[0-9A-Z]{4}){5}\s?[0-9A-Z]{3}(?![0-9A-Za-z])')
IBAN_DOCUMENTAIRES = {'FR7630006000011234567890189', 'FR1420041010050500013M02606'}   # exemples publics des documentations bancaires
EXT_DONNEES = {'.csv', '.tsv', '.json', '.txt', '.md', '.html', '.htm', '.js', '.py', '.xml', '.yml', '.yaml', '.sql'}
DOSSIERS_HORS_DONNEES = {'build', 'dist', 'node_modules', '.git', '__pycache__', 'briques'}
FICHIER_FICTIFS = 'tests/donnees/exemples-fictifs.txt'


def nir_valide(m: re.Match) -> bool:
    departement = {'2A': '19', '2B': '18'}.get(m.group(4), m.group(4))
    corps = int(m.group(1) + m.group(2) + m.group(3) + departement + m.group(5) + m.group(6))
    return 97 - corps % 97 == int(m.group(7))


def iban_valide(texte: str) -> bool:
    compact = re.sub(r'\s', '', texte).upper()
    chiffres = ''.join(str(int(c, 36)) for c in compact[4:] + compact[:4])
    return compact not in IBAN_DOCUMENTAIRES and int(chiffres) % 97 == 1


def valeurs_a_cle_valide(ligne: str) -> list[tuple[str, str]]:
    valeurs = [('numéro de sécurité sociale', m.group(0)) for m in RE_NIR.finditer(ligne) if nir_valide(m)]
    return valeurs + [('IBAN', m.group(0)) for m in RE_IBAN_FR.finditer(ligne) if iban_valide(m.group(0))]


def fichiers_de_donnees(ctx: Contexte) -> list[Chemin]:
    retenus = []
    for p in sorted(ctx.racine.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in EXT_DONNEES or DOSSIERS_HORS_DONNEES & set(p.relative_to(ctx.racine).parts):
            continue
        if ctx.rel(p) != FICHIER_FICTIFS and p.stat().st_size <= 2_000_000:
            retenus.append(p)
    return retenus


def controle_donnees_personnes(ctx: Contexte) -> None:
    """Un numéro de sécurité sociale ou un IBAN dont la clé est juste est presque toujours réel : on arrête tout.

    Un outil qui a besoin d'exemples à clé juste (contrôle de RIB…) les déclare, un par ligne, dans
    tests/donnees/exemples-fictifs.txt : ils sont alors acceptés, et leur nombre figure au bilan.
    """
    declares = {re.sub(r'\s', '', ligne).upper() for ligne in (ctx.texte(ctx.racine / FICHIER_FICTIFS) or '').splitlines()
                if ligne.strip() and not ligne.lstrip().startswith('#')}
    trouvailles, acceptes = [], 0
    for p in fichiers_de_donnees(ctx):
        for numero, ligne in enumerate((ctx.texte(p) or '').splitlines(), 1):
            for nature, valeur in (valeurs_a_cle_valide(ligne) if len(ligne) <= LIGNE_MINIFIEE else []):
                if re.sub(r'\s', '', valeur).upper() in declares:
                    acceptes += 1
                else:
                    trouvailles.append(f'{nature} à clé valide — {ctx.rel(p)}, ligne {numero} ({valeur[:4]}…)')
    for trouvaille in trouvailles[:8]:
        ctx.bilan.erreur(f'Donnée de personne possible : {trouvaille}. Une clé juste signale presque toujours une donnée réelle : '
                         f'la retirer. Si c\'est un exemple inventé, changer un chiffre, ou le déclarer dans {FICHIER_FICTIFS}')
    if len(trouvailles) > 8:
        ctx.bilan.erreur(f'Données de personnes possibles : {len(trouvailles) - 8} autre(s) occurrence(s)')
    if acceptes:
        ctx.bilan.alerte(f'{acceptes} exemple(s) à clé valide déclaré(s) fictif(s) dans {FICHIER_FICTIFS} : à faire confirmer par le référent')
    if not trouvailles:
        ctx.bilan.reussi('Aucun numéro de sécurité sociale ni IBAN à clé valide dans le dossier')


# ================================================================ 16. classe de l'outil (ce que coûte une panne)
def numero_classe(ctx: Contexte) -> int | None:
    m = re.match(r'\s*([123])\b', classe_outil(ctx))
    return int(m.group(1)) if m else None


def controle_classe(ctx: Contexte) -> None:
    """Classe 1 (essentiel) : dossier complet, mode dégradé écrit, restauration essayée dans l'année."""
    classe = numero_classe(ctx)
    if classe != 1:
        return
    if ctx.niveau == NIVEAU_PARTAGE:
        ctx.bilan.erreur('Classe 1 (outil essentiel) : le niveau durable est nécessaire — passer « Niveau : durable » dans le README '
                         '(creer_projet.py, ou remettre_a_niveau.py de la skill d\'entretien)')
        return
    mode = ctx.texte(ctx.racine / 'docs' / 'mode-degrade.md')
    if mode is None:
        ctx.exiger('Classe 1 : docs/mode-degrade.md absent — écrire ce que font les agents si l\'outil est arrêté une journée '
                   '(gabarit : creer_projet.py --classe 1)')
    if ctx.format == 'B':
        date = lire_date(champ_fiche(ctx.texte(ctx.racine / 'docs' / 'fiche-dsi.md') or '', 'Dernier essai de restauration') or '')
        if date is None or date < ctx.aujourdhui - datetime.timedelta(days=365):
            ctx.exiger('Classe 1 : un essai de restauration de moins d\'un an est exigé (docs/fiche-dsi.md)')
    if mode is not None:
        ctx.bilan.reussi('Classe 1 : mode dégradé écrit')


# ================================================================ 14. rôle d'éditeur
RE_LIT_FICHIERS = re.compile(r'FileReader|XLSX\.read|type=["\']file["\']|openpyxl\.load_workbook|\bpd\.read_|pandas\.read_|'
                             r'csv\.(?:reader|DictReader)|readAsArrayBuffer|showOpenFilePicker')
RE_IA = re.compile(r'(?i)\bollama\b|/api/(?:generate|chat)\b|llama[_-]cpp|from transformers|import transformers|\bopenai\b|mistralai|web-llm|@mlc-ai')
RE_PRODUCTION = re.compile(r'jsPDF|Packer\.to(?:Blob|Buffer)|XLSX\.write(?:File)?\(|from docx import|\bimport docx\b|reportlab|'
                           r'Workbook\(\)|window\.print\(|html2pdf|pdfmake')
RE_TRACE = re.compile(r'produitAvec|produit_avec|Produit avec')


def fichiers_qui_contiennent(ctx: Contexte, motif: re.Pattern) -> list[str]:
    """Fichiers du code de l'outil (hors briques communes, module de prise en main et bibliothèques embarquées) qui contiennent le motif."""
    trouves = []
    for p in ctx.fichiers_code(EXT_PYTHON | EXT_WEB):
        relatif = ctx.rel(p)
        if '/briques/' in f'/{relatif}' or p.name in MODULE_PRISE_EN_MAIN:
            continue
        if any(len(ligne) <= LIGNE_MINIFIEE and motif.search(ligne) for ligne in (ctx.texte(p) or '').splitlines()):
            trouves.append(relatif)
    return trouves


def controle_entrees(ctx: Contexte) -> None:
    lit_des_fichiers = fichiers_qui_contiennent(ctx, RE_LIT_FICHIERS)
    texte = ctx.texte(ctx.racine / 'docs' / 'entrees.md')
    lignes = [c for c in lignes_tableau(texte or '') if len(c) >= 4 and c[0] and not RE_MARQUEUR.search(' '.join(c))]
    if not lignes:
        if lit_des_fichiers:
            ctx.bilan.alerte(f'L\'outil lit des fichiers ({", ".join(lit_des_fichiers[:3])}) mais aucune entrée n\'est décrite dans '
                             'docs/entrees.md : décrire chaque format reçu, avec un exemple inventé')
        return
    manques = []
    for cases in lignes:
        exemple = cases[3].strip('` ')
        if not exemple or not (ctx.racine / exemple).exists():
            manques.append(f'« {cases[0]} » ({exemple or "exemple non indiqué"})')
    if manques:
        ctx.exiger('Contrat d\'entrée — fichier exemple absent pour : ' + ', '.join(manques) + ' (un exemple inventé dans tests/donnees/)')
    else:
        ctx.bilan.reussi(f'Contrat d\'entrée : {len(lignes)} format(s) décrit(s), chacun avec son exemple')


def controle_rustine(ctx: Contexte) -> None:
    texte = ctx.texte(ctx.racine / 'docs' / 'rustine.md')
    if texte is None:
        return
    revue = champ_fiche(texte, 'Revue avant le')
    date = lire_date(revue or '')
    signale = (champ_fiche(texte, 'Signalé le') or '').lower()
    if date and date < ctx.aujourdhui:
        ctx.bilan.alerte(f'Rustine à réexaminer (revue prévue le {date.isoformat()}) : le problème de fond est-il réglé ? '
                         'Si oui, l\'outil peut être retiré ; sinon, nouvelle date de revue')
    elif not a_completer(revue) and date is None:
        ctx.bilan.alerte('Fiche rustine : date de revue illisible (écrire JJ/MM/AAAA)')
    if signale.startswith('pas'):
        ctx.bilan.alerte('Le problème de fond n\'est pas encore signalé à qui peut le corriger : le signaler, c\'est préparer le jour '
                         'où cette rustine ne servira plus')
    probleme = champ_fiche(texte, 'Problème de fond')
    if not a_completer(probleme):
        ctx.bilan.reussi(f'Fiche rustine tenue (problème de fond : {probleme})')


def derniere_passe_ia(ctx: Contexte) -> tuple[int, datetime.date | None]:
    lignes = [c for c in lignes_tableau(ctx.texte(ctx.racine / 'tests' / 'ia' / 'questions.md') or '')
              if len(c) >= 4 and c[0] and not RE_MARQUEUR.search(' '.join(c))]
    dates = [d for d in (lire_date(c[3]) for c in lignes) if d]
    return len(lignes), (max(dates) if dates else None)


def controle_ia(ctx: Contexte) -> None:
    usages = fichiers_qui_contiennent(ctx, RE_IA)
    if not usages:
        return
    nombre, derniere = derniere_passe_ia(ctx)
    if not nombre:
        ctx.exiger(f'L\'outil utilise une IA ({", ".join(usages[:3])}) : écrire des questions-tests dans tests/ia/questions.md '
                   '(gabarit : creer_projet.py --ia), à rejouer à chaque changement de modèle')
    elif derniere is None or derniere < ctx.aujourdhui - datetime.timedelta(days=365):
        ctx.bilan.alerte('Questions-tests de la fonction d\'IA : dernier passage absent ou de plus d\'un an — à rejouer')
    else:
        ctx.bilan.reussi(f'Fonction d\'IA : {nombre} question(s)-test(s), rejouées le {derniere.isoformat()}')


def controle_tracabilite(ctx: Contexte) -> None:
    productions = fichiers_qui_contiennent(ctx, RE_PRODUCTION)
    if not productions:
        return
    if fichiers_qui_contiennent(ctx, RE_TRACE):
        ctx.bilan.reussi('Documents produits : mention de traçabilité « Produit avec … » présente')
    else:
        ctx.bilan.alerte(f'L\'outil produit des documents ({", ".join(productions[:3])}) sans la mention « Produit avec <outil> v<version> '
                         'le <date> à partir de … » : utiliser la brique traçabilité (creer_projet.py --briques)')


def controle_editeur(ctx: Contexte) -> None:
    controle_entrees(ctx)
    controle_rustine(ctx)
    controle_ia(ctx)
    controle_tracabilite(ctx)


# ================================================================ fiche DSI, paquet, bilan
def fiche_dsi(ctx: Contexte) -> None:
    fichier = ctx.racine / 'docs' / 'fiche-dsi.md'
    texte = ctx.texte(fichier)
    if texte is None or '<!-- auto:debut -->' not in texte or not ctx.version:
        return
    titre = re.search(r'(?m)^#\s*(.+)$', ctx.texte(ctx.racine / 'README.md') or '')
    vhost = next(iter(sorted((ctx.racine / 'deploy').glob('*.conf'))), None)
    texte_vhost = ctx.texte(vhost) or '' if vhost else ''
    domaine = re.search(r'server_name\s+([^;\s]+)', texte_vhost)
    port = re.search(r'proxy_pass\s+http://127\.0\.0\.1:(\d+)', texte_vhost)
    derogations = [c for c in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'derogations.md') or '') if c and c[0]]
    composants = [c for c in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'composants.md') or '') if c and c[0]]
    lignes = ['| Élément | Valeur |', '|---|---|', f'| Nom | {titre.group(1).strip() if titre else ctx.racine.name} |',
              f'| Version | {ctx.version} |', f'| Format | {ctx.format} |']
    if ctx.format == 'B':
        lignes += [f'| Images | {", ".join(ctx.images) or "—"} |', f'| Port local | 127.0.0.1:{port.group(1) if port else "—"} |',
                   f'| Adresse | https://{domaine.group(1) if domaine else "—"} |', f'| Dossier serveur | /data/apps/{ctx.racine.name} |']
    lignes += [f'| Composants listés | {len(composants)} (voir composants.md) |',
               f'| Exceptions ouvertes | {len(derogations)} (voir derogations.md) |',
               f'| Contrôle fabriqué le | {ctx.aujourdhui.isoformat()} |']
    bloc = '<!-- auto:debut -->\n' + '\n'.join(lignes) + '\n<!-- auto:fin -->'
    neuf = re.sub(r'<!-- auto:debut -->.*?<!-- auto:fin -->', lambda _: bloc, texte, flags=re.S)
    if neuf != texte:
        fichier.write_text(neuf, encoding='utf-8')
        ctx.oublier(fichier)
    ctx.bilan.reussi('Fiche DSI : partie automatique mise à jour')


def exclu(nom_relatif: str) -> bool:
    """Vrai si un élément du chemin doit rester hors du paquet (.env réel, données, dépendances…)."""
    parties = pathlib.PurePosixPath(nom_relatif).parts
    if parties and parties[-1] in FICHIERS_ENV_AUTORISES:
        return any(fnmatch.fnmatch(p, motif) for p in parties[:-1] for motif in EXCLUS_PAQUET)
    return any(fnmatch.fnmatch(p, motif) for p in parties for motif in EXCLUS_PAQUET)


def fabriquer_paquet(ctx: Contexte) -> Chemin:
    """Fabrique le zip et son empreinte SHA-256 (à comparer après tout transfert)."""
    dist = ctx.racine / 'dist'
    dist.mkdir(exist_ok=True)
    nom = f'{ctx.racine.name}_v{ctx.version}' + ('_brouillon' if ctx.brouillon else '')
    cible = dist / f'{nom}.zip'
    with zipfile.ZipFile(cible, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(ctx.racine.rglob('*')):
            relatif = p.relative_to(ctx.racine).as_posix()
            if p.is_file() and not exclu(relatif):
                archive.write(p, f'{ctx.racine.name}_v{ctx.version}/{relatif}')
    empreinte = hashlib.sha256(cible.read_bytes()).hexdigest()
    (dist / f'{nom}.zip.sha256').write_text(f'{empreinte}  {cible.name}\n', encoding='utf-8')
    return cible


def ecrire_bilan(ctx: Contexte, paquet: Chemin | None) -> None:
    dist = ctx.racine / 'dist'
    dist.mkdir(exist_ok=True)
    bilan = ctx.bilan
    lignes = [f'# Bilan de fabrication — {ctx.racine.name} v{ctx.version or "?"}', '', f'Date : {ctx.aujourdhui.isoformat()}',
              f'Contrôle : fabriquer.py {VERSION_CONTROLE}', '']
    rubriques = (('Réussi', bilan.ok), ('Erreurs (bloquantes)', bilan.erreurs), ('Alertes', bilan.alertes), ('Non testé', bilan.non_testes))
    for titre, elements in rubriques:
        lignes += [f'## {titre}', *([f'- {e}' for e in elements] or ['- aucun']), '']
    lignes.append(f'Paquet : {paquet.name if paquet else "non fabriqué"}')
    (dist / 'bilan-fabrication.md').write_text('\n'.join(lignes) + '\n', encoding='utf-8')


def titre_outil(ctx: Contexte) -> str:
    titre = re.search(r'(?m)^#\s*(.+)$', ctx.texte(ctx.racine / 'README.md') or '')
    return titre.group(1).strip() if titre else ctx.racine.name


def a_quoi_ca_sert(ctx: Contexte) -> str:
    """La première ligne écrite sous « À quoi sert l'outil » dans le README ; chaîne vide si elle reste à compléter."""
    bloc = re.search(r"(?ms)^##\s*À quoi sert l'outil\s*\n(.*?)(?=^##|\Z)", ctx.texte(ctx.racine / 'README.md') or '')
    ligne = next((ligne.strip() for ligne in (bloc.group(1) if bloc else '').splitlines() if ligne.strip()), '')
    return '' if RE_MARQUEUR.search(ligne) else ligne


def statut_transmission(ctx: Contexte) -> str:
    """Où en est l'outil, dit en une phrase pour la cellule opérationnelle."""
    bilan = ctx.bilan
    if ctx.niveau == NIVEAU_PARTAGE:
        return 'À corriger avant de le partager' if bilan.erreurs else 'Utilisable par des collègues (niveau partagé)'
    if bilan.erreurs:
        return 'À retravailler avant installation'
    if ctx.brouillon:
        return 'Brouillon : pas encore transmissible'
    return 'Installable avec réserves' if bilan.alertes else 'Prêt à installer'


def ecrire_dossier(ctx: Contexte, paquet: Chemin | None) -> None:
    """Résumé d'une page pour la cellule opérationnelle : écrit même quand des points restent à corriger."""
    dist = ctx.racine / 'dist'
    dist.mkdir(exist_ok=True)
    partage = ctx.texte(ctx.racine / 'docs' / 'partage.md') or ''
    def champ(libelle: str) -> str:
        valeur = champ_fiche(partage, libelle)
        return 'non renseigné' if a_completer(valeur) else str(valeur)

    exceptions = [c[0] for c in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'derogations.md') or '')
                  if c and c[0] and not RE_MARQUEUR.search(' '.join(c))]
    bilan = ctx.bilan
    lignes = [f'# Dossier de transmission — {titre_outil(ctx)} v{ctx.version or "?"}', '', f'**Statut : {statut_transmission(ctx)}**', '',
              f'- Niveau : {ctx.niveau} · format {ctx.format} · contrôlé le {ctx.aujourdhui.isoformat()}',
              f'- À quoi il sert : {a_quoi_ca_sert(ctx) or "non renseigné"}',
              f'- Réutilisable par d\'autres : {champ("Potentiel de réutilisation")} · cellule informée : {champ("Cellule opérationnelle informée")}',
              '- Installation souhaitée : ' + champ("Demande d'installation"),
              f'- Exceptions ouvertes : {", ".join(exceptions) or "aucune"}',
              f'- Paquet : {paquet.name if paquet else "non fabriqué"}', '']
    rubriques = (('En ordre', bilan.ok), ('À corriger avant de transmettre', bilan.erreurs),
                 ('À regarder', bilan.alertes), ('Non testé', bilan.non_testes))
    for titre, elements in rubriques:
        lignes += [f'## {titre}', *([f'- {e}' for e in elements] or ['- rien']), '']
    (dist / 'dossier-transmission.md').write_text('\n'.join(lignes) + '\n', encoding='utf-8')


FORMATS_EN_CLAIR = {'A': 'fichier HTML autonome', 'B': 'application web sur serveur',
                    'C': 'programme installé sur les postes (MSI)', 'D': 'document Grist'}


def valeur_readme(ctx: Contexte, libelle: str) -> str:
    """Valeur d'une ligne « - Libellé : valeur » du README ; « à compléter » si elle manque ou reste à remplir."""
    valeur = champ_fiche(ctx.texte(ctx.racine / 'README.md') or '', libelle)
    return 'à compléter' if a_completer(valeur) else str(valeur)


def premiere_ligne_section(ctx: Contexte, titre: str) -> str:
    bloc = re.search(rf'(?ms)^##\s*{titre}\s*\n(.*?)(?=^##|\Z)', ctx.texte(ctx.racine / 'README.md') or '')
    ligne = next((ligne.strip() for ligne in (bloc.group(1) if bloc else '').splitlines() if ligne.strip()), '')
    return 'à compléter' if a_completer(ligne) else ligne


def classe_outil(ctx: Contexte) -> str:
    m = re.search(r'(?im)^Classe\s*:\s*(.*)$', ctx.texte(ctx.racine / 'README.md') or '')
    return 'à compléter' if not m or a_completer(m.group(1)) else m.group(1).strip()


def ou_le_trouver(ctx: Contexte) -> str:
    valeur = valeur_readme(ctx, 'Où le trouver')
    vhost = next(iter(sorted((ctx.racine / 'deploy').glob('*.conf'))), None)
    domaine = re.search(r'server_name\s+([^;\s]+)', ctx.texte(vhost) or '') if vhost and ctx.format == 'B' else None
    return f'https://{domaine.group(1)}' if valeur == 'à compléter' and domaine else valeur


def resume_composants(ctx: Contexte) -> str:
    lignes = [c for c in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'composants.md') or '')
              if len(c) >= 4 and c[0] and not RE_MARQUEUR.search(' '.join(c))]
    dates = [d for d in (lire_date(c[3]) for c in lignes) if d]
    prochaine = min(dates).isoformat() if dates else 'non renseignée'
    return f'{len(lignes)} listé(s) · prochaine fin de support : {prochaine}'


def ligne_rustine(ctx: Contexte) -> str:
    texte = ctx.texte(ctx.racine / 'docs' / 'rustine.md')
    if texte is None:
        return 'Rustine : non'
    probleme, proprietaire = champ_fiche(texte, 'Problème de fond'), champ_fiche(texte, 'À qui il appartient')
    return (f'Rustine : oui — problème de fond : {"à compléter" if a_completer(probleme) else probleme} '
            f'(appartient à : {"à compléter" if a_completer(proprietaire) else proprietaire})')


def ligne_ia(ctx: Contexte) -> str:
    if not fichiers_qui_contiennent(ctx, RE_IA):
        return 'Fonction d\'IA : non'
    _, derniere = derniere_passe_ia(ctx)
    return f'Fonction d\'IA : oui — questions-tests rejouées le {derniere.strftime("%d/%m/%Y") if derniere else "à faire"}'


def ecrire_fiche_registre(ctx: Contexte, paquet: Chemin | None) -> None:
    """Texte prêt à coller dans la carte de l'outil, sur le registre des outils de la collectivité."""
    partage = ctx.texte(ctx.racine / 'docs' / 'partage.md') or ''
    potentiel = champ_fiche(partage, 'Potentiel de réutilisation')
    exceptions = [c for c in lignes_tableau(ctx.texte(ctx.racine / 'docs' / 'derogations.md') or '')
                  if c and c[0] and not RE_MARQUEUR.search(' '.join(c))]
    lignes = [f'Outil : {titre_outil(ctx)} — version {ctx.version or "?"}',
              'Nature : outil maison (dossier de la skill fabrique-outils)',
              f'À quoi il sert : {a_quoi_ca_sert(ctx) or "à compléter"}',
              f'Format : {FORMATS_EN_CLAIR.get(ctx.format, ctx.format)} · niveau {ctx.niveau}',
              f'Classe : {classe_outil(ctx)}' + ((' · mode dégradé : ' + ('écrit' if (ctx.racine / 'docs' / 'mode-degrade.md').exists() else 'à écrire'))
                                                  if numero_classe(ctx) == 1 else ''),
              f'Service demandeur : {valeur_readme(ctx, "Service demandeur")}',
              f'Référent métier : {valeur_readme(ctx, "Référent")}',
              f'Suppléant : {valeur_readme(ctx, "Suppléant")}',
              f"Chef de projet chargé de l'entretien : {valeur_readme(ctx, 'Chef de projet')}",
              f'Où le trouver : {ou_le_trouver(ctx)}',
              f'Dossier (code et documentation) : {premiere_ligne_section(ctx, "Dépôt du code")}',
              f'Documentation : {valeur_readme(ctx, "Documentation")}',
              f'Contrôle de sécurité : {valeur_readme(ctx, "Niveau du contrôle de sécurité")}',
              f'Composants : {resume_composants(ctx)}',
              f'Exceptions ouvertes : {len(exceptions)}',
              ligne_rustine(ctx),
              ligne_ia(ctx),
              f'Dernier contrôle : {ctx.aujourdhui.strftime("%d/%m/%Y")} — {statut_transmission(ctx)} (contrôle {VERSION_CONTROLE})',
              f"Réutilisable par d'autres : {'à compléter' if a_completer(potentiel) else potentiel}",
              f'Paquet : {paquet.name if paquet else "non fabriqué"}']
    dist = ctx.racine / 'dist'
    dist.mkdir(exist_ok=True)
    (dist / 'fiche-registre.txt').write_text('\n'.join(lignes) + '\n', encoding='utf-8')


def afficher(ctx: Contexte, paquet: Chemin | None) -> int:
    bilan = ctx.bilan
    print(f'\nContrôle de {ctx.racine.name} (format {ctx.format}, version {ctx.version or "?"})\n')
    for signe, messages in (('✓', bilan.ok), ('!', bilan.alertes), ('✗', bilan.erreurs)):
        for message in messages:
            print(f'  {signe} {message}')
    for message in bilan.non_testes:
        print('  · non testé : ' + message)
    print(f'\nStatut : {statut_transmission(ctx)} (résumé pour la cellule : dist/dossier-transmission.md ; '
          'fiche à coller dans la fiche du registre : dist/fiche-registre.txt)')
    if bilan.erreurs:
        print(f'RÉSULTAT : {len(bilan.erreurs)} point(s) à corriger avant de transmettre. Aucun paquet fabriqué. '
              'Ce contrôle ne vous empêche pas d\'utiliser l\'outil : il sert à ce que la cellule puisse l\'installer ensuite.')
        return 1
    bilan_alertes = f'aucun point bloquant, {len(bilan.alertes)} point(s) à regarder' if bilan.alertes else 'tout est cohérent'
    print(f'RÉSULTAT : {bilan_alertes}.' + (f' Paquet fabriqué : {paquet}' if paquet else ' (aucun paquet demandé)'))
    if ctx.brouillon:
        print('Fabriqué en mode brouillon : à compléter avant de le transmettre à la cellule.')
    return 0


# ================================================================ programme principal
def lire_options(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(prog='fabriquer.py', description='Contrôle un projet d\'outil et fabrique son paquet.')
    analyseur.add_argument('dossier', nargs='?', default='.', help='dossier du projet (par défaut : le dossier courant)')
    analyseur.add_argument('--brouillon', action='store_true',
                           help='contrôle d\'étape pour travailler librement : la complétude (champs, SPEC validée, tests, composants) devient une alerte ; '
                                'secrets, appels externes, code dangereux et tests en échec restent bloquants')
    analyseur.add_argument('--sans-paquet', action='store_true', help='contrôle seulement, sans fabriquer le zip')
    analyseur.add_argument('--sans-tests', action='store_true', help='ne lance pas les tests (accepté seulement avec --brouillon)')
    analyseur.add_argument('--exiger-analyses', action='store_true',
                           help='un outil d\'analyse absent (ruff, bandit, gitleaks, pip-audit, node…) devient une erreur')
    analyseur.add_argument('--analyser-images', action='store_true', help='analyse les images du compose avec trivy (long, réseau)')
    analyseur.add_argument('--delai-tests', type=int, default=300, metavar='SECONDES', help='durée maximale d\'une commande de test')
    analyseur.add_argument('--date', type=datetime.date.fromisoformat, default=None, metavar='AAAA-MM-JJ',
                           help='date du jour imposée (pour des contrôles reproductibles)')
    return analyseur.parse_args(argv)


def preparer(options: argparse.Namespace) -> Contexte:
    racine = Chemin(options.dossier).resolve()
    if racine.name == 'build':
        racine = racine.parent
    if not (racine / 'README.md').exists() or not (racine / 'SPEC.md').exists():
        sys.exit(f'Arrêt : {racine} ne ressemble pas à un projet d\'outil (README.md et SPEC.md attendus).')
    ctx = Contexte(racine=racine, format='A', brouillon=options.brouillon, aujourdhui=options.date or datetime.date.today(),
                   exiger_analyses=options.exiger_analyses, sans_tests=options.sans_tests,
                   analyser_images=options.analyser_images, delai=options.delai_tests)
    readme = ctx.texte(racine / 'README.md') or ''
    m = re.search(r'(?im)^Format\s*:\s*([ABCD])\b', readme)
    if m:
        ctx.format = m.group(1).upper()
    else:
        ctx.bilan.erreur('README.md : ligne « Format : A, B, C ou D » absente (contrôles faits comme pour un format A)')
    niveau = re.search(r'(?im)^Niveau\s*:\s*(partag[ée]|durable)\b', readme)
    if niveau and niveau.group(1).lower().startswith('partag'):
        ctx.niveau = NIVEAU_PARTAGE
    if ctx.niveau == NIVEAU_PARTAGE and ctx.format != 'A':
        ctx.bilan.erreur('README.md : le niveau partagé ne convient qu\'au format A (un simple fichier). '
                         'Un outil sur serveur, sur poste ou dans Grist est durable : écrire « Niveau : durable »')
    return ctx


def controler(ctx: Contexte) -> None:
    controle_fichiers(ctx)
    controle_donnees_personnes(ctx)
    controle_version(ctx)
    controle_regles(ctx)
    controle_tests(ctx)
    controle_code(ctx)
    controle_secrets(ctx)
    controle_reseau(ctx)
    requirements, verrous = controle_dependances(ctx)
    if ctx.format == 'B':
        controle_integration(ctx)
    controle_analyses(ctx, requirements, verrous)
    controle_composants(ctx)
    controle_suivi(ctx)
    controle_partage(ctx)
    controle_editeur(ctx)
    controle_classe(ctx)
    fiche_dsi(ctx)


def main(argv: list[str]) -> int:
    options = lire_options(argv)
    ctx = preparer(options)
    controler(ctx)
    paquet = None
    if not ctx.bilan.erreurs and not options.sans_paquet and ctx.version:
        paquet = fabriquer_paquet(ctx)
    ecrire_bilan(ctx, paquet)
    ecrire_dossier(ctx, paquet)
    ecrire_fiche_registre(ctx, paquet)
    return afficher(ctx, paquet)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
