"""Autotest de creer_projet.py et fabriquer.py : la skill vérifie ses propres garde-fous.

Usage : python3 autotest_fabrique.py
À lancer avant chaque nouvelle version de la skill. Crée des projets fictifs dans un dossier temporaire,
provoque volontairement des erreurs (test en échec, port ouvert, secret, version décalée, appel externe…) et
vérifie que fabriquer.py les refuse, puis qu'un projet correct est accepté et empaqueté sans .env.
Les cas qui dépendent d'un outil (node, ruff) sont sautés, et signalés, si l'outil est absent.
Code de sortie 0 si tout est bon.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

SC = pathlib.Path(__file__).resolve().parent
DATE = '2026-11-13'
echecs: list[str] = []
sautes: list[str] = []

TEST_CORRECT = '''"""Tests des règles RG-01 et RG-02 (données inventées)."""
from src.coeur.regles import total


def test_rg01_le_total_est_la_somme_des_lignes():
    assert total([1, 2]) == 3


def test_rg02_une_ligne_vide_est_ignoree():
    assert total([1, None, 2]) == 3
'''
REGLES = '''"""Cœur métier de la démonstration."""
APP_VERSION = '0.1.0'


def total(lignes):
    # RG-01 : total = somme des lignes
    # RG-02 : une ligne vide est ignorée
    return sum(x for x in lignes if x)
'''
COMPOSANTS = '''# Composants — demo

Version documentée : 0.1.0

| Composant | Version | Rôle | Fin de support | Source de la date |
|---|---|---|---|---|
| nginx | 1.27.3 | serveur web | 2027-06 | page de l'éditeur |
| Python | 3.12 | calcul | 2028-10 | python.org |
'''


# ---------------------------------------------------------------- outils du test
def run(script: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    environnement = {**os.environ, 'PYTHONIOENCODING': 'utf-8', **(env or {})}
    return subprocess.run([sys.executable, str(SC / script), *args], capture_output=True, text=True, encoding='utf-8',
                          errors='replace', env=environnement, check=False)


def fabriquer(projet: pathlib.Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return run('fabriquer.py', str(projet), '--date', DATE, *args, env=env)


def verifier(condition: bool, libelle: str, detail: str = '') -> None:
    print(('  ✓ ' if condition else '  ✗ ') + libelle)
    if not condition:
        echecs.append(libelle)
        if detail:
            print('      ' + detail.strip().replace('\n', '\n      ')[:1500])


def lire(chemin: pathlib.Path) -> str:
    return chemin.read_text(encoding='utf-8')


def ecrire(relatif: str, texte: str):
    def modifier(projet: pathlib.Path) -> None:
        cible = projet / relatif
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding='utf-8')
    return modifier


def remplacer(relatif: str, avant: str, apres: str):
    def modifier(projet: pathlib.Path) -> None:
        cible = projet / relatif
        texte = lire(cible)
        assert avant in texte, f'{relatif} ne contient pas « {avant} » : le cas de test est à revoir'
        cible.write_text(texte.replace(avant, apres, 1), encoding='utf-8')
    return modifier


def substituer(relatif: str, motif: str, apres: str):
    def modifier(projet: pathlib.Path) -> None:
        cible = projet / relatif
        cible.write_text(re.sub(motif, apres, lire(cible)), encoding='utf-8')
    return modifier


def completer(projet: pathlib.Path) -> None:
    """Remplit un projet fraîchement créé de façon minimale mais valide."""
    for fichier in list(projet.rglob('*')):
        if fichier.is_file() and fichier.suffix in ('.md', '.yaml', '.yml', '.txt', '.conf') and fichier.parent.name != 'build':
            texte = lire(fichier)
            complet = re.sub(r'À[ _-]?COMPLÉTER', 'renseigné', texte)
            if complet != texte:
                fichier.write_text(complet, encoding='utf-8')
    readme = re.sub(r'(?m)^Classe : .*$', 'Classe : 2 (important)', lire(projet / 'README.md'))
    (projet / 'README.md').write_text(readme, encoding='utf-8')
    spec = lire(projet / 'SPEC.md')
    spec = re.sub(r'(?m)^> .*renseigné.*\n\n?', '', spec)
    spec = re.sub(r'(?m)^Statut : .*$', 'Statut : validée le 13/11/2026 par la cellule opérationnelle', spec, count=1)
    spec = re.sub(r'(?m)^- RG-01 — .*$', '- RG-01 — Un total est égal à la somme des lignes.\n- RG-02 — Une ligne vide est ignorée.', spec, count=1)
    (projet / 'SPEC.md').write_text(spec, encoding='utf-8')
    ecrire('src/coeur/regles.py', REGLES)(projet)
    ecrire('tests/test_regles.py', TEST_CORRECT)(projet)
    ecrire('docs/composants.md', COMPOSANTS)(projet)


class Banc:
    """Un projet de référence correct, dont chaque cas modifie une copie."""

    def __init__(self, base: pathlib.Path, travail: pathlib.Path):
        self.base, self.travail, self.numero = base, travail, 0

    def copie(self) -> pathlib.Path:
        self.numero += 1
        return pathlib.Path(shutil.copytree(self.base, self.travail / f'cas-{self.numero:03d}'))

    def cas(self, libelle: str, modifier, code_attendu: int, mot: str | None = None, options: tuple = (), env: dict | None = None,
            absent: str | None = None) -> pathlib.Path:
        projet = self.copie()
        modifier(projet)
        resultat = fabriquer(projet, '--sans-paquet', *options, env=env)
        conforme = resultat.returncode == code_attendu and (mot is None or mot.lower() in resultat.stdout.lower()) \
            and (absent is None or absent.lower() not in resultat.stdout.lower())
        verifier(conforme, libelle, resultat.stdout + resultat.stderr)
        return projet

    def refuse(self, libelle: str, modifier, mot: str, **options) -> pathlib.Path:
        return self.cas(libelle, modifier, 1, mot, **options)

    def accepte(self, libelle: str, modifier, mot: str | None = None, **options) -> pathlib.Path:
        return self.cas(libelle, modifier, 0, mot, **options)


def charger_fabriquer():
    """Charge fabriquer.py comme un module, pour essayer directement ses fonctions."""
    spec = importlib.util.spec_from_file_location('fabriquer', SC / 'fabriquer.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['fabriquer'] = module
    spec.loader.exec_module(module)
    return module


def si_outil(outil: str, libelle: str) -> bool:
    if shutil.which(outil):
        return True
    sautes.append(f'{libelle} (« {outil} » absent)')
    print(f'  · sauté : {libelle} (« {outil} » absent)')
    return False


# ---------------------------------------------------------------- les familles de cas
def essais_creation(tmp: pathlib.Path) -> pathlib.Path:
    print('\n— Création d\'un projet de format B')
    r = run('creer_projet.py', 'demo-outil', '--format', 'B', '--titre', 'Outil de démonstration', '--dest', str(tmp),
            '--port', '8150', '--image', 'nginx:1.27.3')
    projet = tmp / 'demo-outil'
    verifier(r.returncode == 0 and (projet / 'deploy' / 'compose.yaml').exists(), 'projet B créé avec son dossier deploy/', r.stdout + r.stderr)
    attendus = ['deploy/.env.exemple', '.gitignore', 'build/fabriquer.py', 'docs/decisions.md', 'docs/partage.md',
                'deploy/playbook_deploy.yaml', 'deploy/playbook_check.yaml']
    verifier(all((projet / f).exists() for f in attendus), 'gabarits présents (.env.exemple, .gitignore, fabriquer.py, décisions, partage, playbooks)')
    r = run('creer_projet.py', 'demo-outil', '--format', 'B', '--dest', str(tmp))
    verifier(r.returncode != 0 and 'existe déjà' in (r.stdout + r.stderr), 'un dossier existant n\'est jamais écrasé')
    r = run('creer_projet.py', 'Nom Invalide', '--format', 'B', '--dest', str(tmp))
    verifier(r.returncode != 0, 'un nom court invalide est refusé')
    return projet


def essais_projet_vierge_puis_complet(projet: pathlib.Path) -> None:
    print('\n— Projet vierge : le contrôle doit refuser')
    r = fabriquer(projet)
    verifier(r.returncode == 1 and 'À COMPLÉTER' in r.stdout and not list((projet / 'dist').glob('*.zip')),
             'refus sur un projet vierge, aucun paquet fabriqué', r.stdout)
    r = fabriquer(projet, '--brouillon', '--sans-paquet')
    verifier('aucune règle de gestion' in r.stdout, 'même en brouillon, une SPEC sans règle est signalée', r.stdout)

    print('\n— Projet complété : le contrôle doit accepter')
    completer(projet)
    r = fabriquer(projet)
    paquets = list((projet / 'dist').glob('*.zip'))
    verifier(r.returncode == 0 and len(paquets) == 1, 'projet correct accepté, paquet fabriqué', r.stdout + r.stderr)
    verifier('Tests exécutés' in r.stdout, 'les tests ont réellement été exécutés', r.stdout)
    verifier('restauration' in r.stdout.lower(), 'format B : l\'essai de restauration manquant est rappelé', r.stdout)
    if paquets:
        noms = zipfile.ZipFile(paquets[0]).namelist()
        verifier(any(n.endswith('deploy/.env.exemple') for n in noms) and not any(n.endswith('/.env') for n in noms)
                 and not any('/dist/' in n for n in noms), 'le paquet contient .env.exemple, jamais .env ni dist/')
        empreinte = projet / 'dist' / (paquets[0].name + '.sha256')
        verifier(empreinte.exists() and lire(empreinte).split()[0] == hashlib.sha256(paquets[0].read_bytes()).hexdigest(),
                 'l\'empreinte SHA-256 du paquet est écrite et exacte')
    fiche = lire(projet / 'docs' / 'fiche-dsi.md')
    verifier('127.0.0.1:8150' in fiche and 'demo-outil.exemple.fr' in fiche and 'nginx:1.27.3' in fiche and DATE in fiche,
             'la fiche DSI automatique reprend image, port, adresse et date imposée')
    verifier((projet / 'dist' / 'bilan-fabrication.md').exists() and (projet / 'dist' / 'tests-sortie.txt').exists(),
             'le bilan de fabrication et la sortie des tests sont écrits')
    fiche_registre = lire(projet / 'dist' / 'fiche-registre.txt') if (projet / 'dist' / 'fiche-registre.txt').exists() else ''
    verifier('Outil : Outil de démonstration — version 0.1.0' in fiche_registre and 'Où le trouver : https://demo-outil.exemple.fr' in fiche_registre
             and 'Dernier contrôle : 13/11/2026' in fiche_registre and 'Composants : 2 listé(s) · prochaine fin de support : 2027-06-30' in fiche_registre,
             'la fiche du registre est écrite, remplie depuis le dossier', fiche_registre)


def essais_tests(banc: Banc) -> None:
    print('\n— Exécution des tests')
    banc.refuse('un test en échec est refusé', remplacer('tests/test_regles.py', '== 3', '== 4'), 'Tests en échec')
    banc.refuse('des tests sans fonction « test_ » sont refusés',
                ecrire('tests/test_regles.py', '# RG-01 RG-02\nassert True\n'), 'Aucun test n\'a tourné')
    banc.refuse('un dossier tests/ sans test exécutable est refusé',
                lambda q: ((q / 'tests' / 'test_regles.py').unlink(), ecrire('tests/donnees.json', '{"RG-01": 1, "RG-02": 2}')(q)),
                'Aucun test exécutable')
    banc.refuse('--sans-tests est refusé pour une livraison', lambda q: None, 'exige des tests', options=('--sans-tests',))
    banc.accepte('--sans-tests est accepté en brouillon, et signalé', lambda q: None, 'Tests non exécutés',
                 options=('--sans-tests', '--brouillon'))
    banc.accepte('une commande de test déclarée dans build/controles.json est utilisée',
                 ecrire('build/controles.json', '{"tests": [["' + sys.executable.replace('\\', '/') + '", "-c", "print(42)"]]}'),
                 'Tests exécutés')
    projet = banc.copie()
    lanceur_integre = charger_fabriquer().MINI_LANCEUR
    def lanceur(fichier: str) -> int:
        return subprocess.run([sys.executable, '-c', lanceur_integre, fichier], cwd=projet, capture_output=True, check=False).returncode
    verifier(lanceur('tests/test_regles.py') == 0, 'lanceur intégré (sans pytest) : des tests corrects passent')
    remplacer('tests/test_regles.py', '== 3', '== 4')(projet)
    verifier(lanceur('tests/test_regles.py') == 1, 'lanceur intégré : un test en échec est vu')
    ecrire('tests/test_vide.py', 'x = 1\n')(projet)
    verifier(lanceur('tests/test_vide.py') == 5, 'lanceur intégré : un fichier sans fonction de test est vu')
    if si_outil('node', 'tests JavaScript exécutés par node'):
        test_js = "const test = require('node:test');\nconst assert = require('node:assert');\n// RG-01\ntest('somme', () => assert.strictEqual(1 + 2, {attendu}));\n"
        banc.accepte('un test JavaScript correct (node --test) passe', ecrire('tests/somme.test.js', test_js.format(attendu=3)), 'Tests exécutés')
        banc.refuse('un test JavaScript en échec est refusé', ecrire('tests/somme.test.js', test_js.format(attendu=4)), 'Tests en échec')


def essais_code(banc: Banc) -> None:
    print('\n— Qualité et sûreté du code')
    banc.refuse('une erreur de syntaxe Python est refusée', ecrire('src/coeur/casse.py', 'def f(:\n    pass\n'), 'syntaxe Python')
    banc.refuse('un « except: » sans type est refusé',
                ecrire('src/coeur/avale.py', 'def f():\n    try:\n        return 1\n    except:\n        return 0\n'), 'sans type')
    banc.accepte('une erreur avalée sans commentaire donne une alerte',
                 ecrire('src/coeur/avale.py', 'def f():\n    try:\n        return 1\n    except ValueError:\n        pass\n'), 'avalée en silence')
    banc.refuse('shell=True est refusé',
                ecrire('src/coeur/commande.py', 'import subprocess\n\n\ndef f(x):\n    return subprocess.run("ls " + x, shell=True)\n'), 'shell=True')
    banc.refuse('une requête SQL construite avec du texte est refusée',
                ecrire('src/coeur/base.py', 'def f(cur, nom):\n    cur.execute(f"SELECT * FROM t WHERE nom = \'{nom}\'")\n'), 'paramétrée')
    banc.accepte('une requête SQL paramétrée avec LIKE est acceptée',
                 ecrire('src/coeur/base.py', 'def f(cur, nom):\n    cur.execute("SELECT * FROM t WHERE nom LIKE \'%a\' AND x = ?", (nom,))\n'),
                 absent='paramétrée')
    banc.refuse('eval() dans du JavaScript est refusé', ecrire('src/calc.js', 'function f(x) { return eval(x); }\n'), 'eval()')
    banc.accepte('le même eval() justifié par « nosec : raison » est accepté',
                 ecrire('src/calc.js', 'function f() { return eval("1+1"); } // nosec : expression fixe\n'))
    banc.accepte('innerHTML donne une alerte de relecture, sans bloquer',
                 ecrire('src/page.js', 'function f(el, t) { el.innerHTML = t; }\n'), 'innerHTML')
    banc.accepte('le stockage du navigateur donne un rappel sur les données de personnes',
                 ecrire('src/page.js', 'function f(v) { localStorage.setItem("k", v); }\n'), 'Stockage du navigateur')
    if si_outil('node', 'syntaxe JavaScript'):
        banc.refuse('une erreur de syntaxe JavaScript est refusée', ecrire('src/casse.js', 'function f( {\n'), 'syntaxe JavaScript')
        banc.refuse('une erreur de syntaxe dans un <script> de page HTML est refusée',
                    ecrire('src/page.html', '<html><body><script>function f( {</script></body></html>\n'), 'bloc <script>')
        banc.accepte('un module JavaScript écrit dans un fichier .js est accepté',
                     ecrire('src/module.js', 'export function f() { return 1; }\n'), 'JavaScript : syntaxe correcte')
    if si_outil('ruff', 'analyse ruff'):
        banc.refuse('un nom inconnu repéré par ruff est refusé',
                    ecrire('src/coeur/inconnu.py', 'def f():\n    return valeur_jamais_definie\n'), 'ruff')


def essais_dependances(banc: Banc, chemin_vide: dict) -> None:
    print('\n— Dépendances et images')
    banc.refuse('une dépendance Python non figée est refusée', ecrire('requirements.txt', 'flask>=3.0\n'), 'non figées')
    banc.accepte('des dépendances figées sont acceptées (sans outil d\'analyse)',
                 ecrire('requirements.txt', 'flask==3.0.3\n'), 'toutes figées', env=chemin_vide)
    banc.refuse('un package.json sans verrou est refusé',
                ecrire('package.json', '{"name": "demo", "version": "0.1.0", "dependencies": {"leftpad": "1.0.0"}}\n'), 'package-lock.json')
    banc.refuse('un Dockerfile sur une image « latest » est refusé',
                ecrire('deploy/Dockerfile', 'FROM python:latest\nUSER 10001\n'), 'sans version précise')
    banc.refuse('un Dockerfile sans version d\'image est refusé', ecrire('deploy/Dockerfile', 'FROM python\nUSER 10001\n'), 'sans version précise')
    banc.refuse('un secret dans un Dockerfile est refusé',
                ecrire('deploy/Dockerfile', 'FROM python:3.12.8-slim\nENV APP_SECRET=Zx9pLm22qq\nUSER 10001\n'), 'secret écrit dans le Dockerfile')
    banc.accepte('un Dockerfile à étapes, figé et non root, est accepté',
                 ecrire('deploy/Dockerfile', 'FROM python:3.12.8-slim AS base\nFROM base\nENV KEYCLOAK_URL=x\nUSER 10001\n'), 'image de base figée')
    banc.accepte('un Dockerfile en root donne une alerte', ecrire('deploy/Dockerfile', 'FROM python:3.12.8-slim\n'), 'tourne en root')


def essais_socle(banc: Banc) -> None:
    print('\n— Secrets, versions, règles, composants, serveur')
    compose, vhost = 'deploy/compose.yaml', 'deploy/demo-outil.conf'
    banc.refuse('un fichier .env réel dans le dossier est refusé', ecrire('.env', 'X=1\n'), '.env')
    banc.refuse('un fichier .env.local est refusé aussi', ecrire('deploy/.env.local', 'X=1\n'), '.env.local')
    banc.refuse('un port publié sur toutes les interfaces est refusé', remplacer(compose, '"127.0.0.1:8150:80"', '"8150:80"'), 'toutes les interfaces')
    banc.refuse('une image « latest » est refusée', remplacer(compose, 'nginx:1.27.3', 'nginx:latest'), 'sans version précise')
    banc.refuse('« restart: always » manquant est refusé', remplacer(compose, 'restart: always', 'restart: unless-stopped'), 'restart: always')
    banc.refuse('un secret écrit en clair dans le compose est refusé',
                remplacer(compose, '    read_only: true', '    environment:\n      APP_PASSWORD: Zx9pLm22qq\n    read_only: true'), 'en clair')
    banc.accepte('un compose indenté de 4 espaces est compris',
                 lambda q: (q / compose).write_text(re.sub(r'(?m)^( +)', lambda m: m.group(1) * 2, lire(q / compose)), encoding='utf-8'),
                 'Compose conforme')
    banc.refuse('un mot de passe en dur dans le code est refusé', ecrire('src/coeur/acces.py', 'password = "abcdef123"\n'), 'écrit en dur')
    banc.accepte('le même exemple fictif balisé « nosecret » est accepté',
                 ecrire('src/coeur/acces.py', 'password = "abcdef123"  # nosecret : exemple fictif\n'))
    banc.refuse('une version décalée dans le README est refusée', remplacer('README.md', 'Version : 0.1.0', 'Version : 0.2.0'), 'non alignée')
    banc.refuse('un README sans ligne « Format » est refusé', substituer('README.md', r'(?m)^Format : .*\n', ''), 'Format')
    banc.refuse('une constante APP_VERSION décalée est refusée', remplacer('src/coeur/regles.py', '0.1.0', '0.0.9'), 'APP_VERSION')
    banc.refuse('une règle sans test est refusée',
                ecrire('tests/test_regles.py', TEST_CORRECT.replace('RG-02', 'autre règle').replace('rg02', 'autre')), 'sans test')
    banc.refuse('une règle jamais citée dans le code est refusée', remplacer('src/coeur/regles.py', '# RG-02', '# autre règle'), 'jamais citées')
    banc.refuse('une SPEC non validée est refusée', substituer('SPEC.md', r'(?m)^Statut : .*$', 'Statut : brouillon'), 'statut')
    banc.refuse('un composant dont le support est terminé est refusé', remplacer('docs/composants.md', '2027-06', '2026-06'), 'support terminé')
    banc.refuse('un composant noté « plus maintenu » est refusé, même avec une source',
                remplacer('docs/composants.md', '2027-06', 'plus maintenu'), 'support terminé')
    banc.refuse('une image du compose absente de composants.md est refusée', remplacer('docs/composants.md', 'nginx', 'serveur'), 'n\'est pas listée')
    banc.refuse('une ouverture externe sans décision écrite (pas de deny all) est refusée', remplacer(vhost, 'deny all;', ''), 'deny all')
    banc.accepte('un essai de restauration daté est reconnu',
                 substituer('docs/fiche-dsi.md', r'(?m)^(- Dernier essai de restauration[^:\n]*:).*$', r'\1 02/11/2026'), 'restauration essayée')


def essais_reseau(banc: Banc) -> None:
    print('\n— Appels réseau')
    page = '<html><head><script src="https://cdn.exemple-externe.org/lib.js"></script></head></html>'
    projet = banc.refuse('une bibliothèque chargée depuis un CDN est refusée', ecrire('src/page.html', page), 'cdn.exemple-externe.org')
    ecrire('reseau-autorise.txt', 'cdn.exemple-externe.org   essai\n')(projet)
    r = fabriquer(projet, '--sans-paquet')
    verifier(r.returncode == 0, 'le même hôte déclaré avec sa raison est accepté', r.stdout)
    ecrire('reseau-autorise.txt', 'cdn.exemple-externe.org\n')(projet)
    r = fabriquer(projet, '--sans-paquet')
    verifier(r.returncode == 1 and 'sans raison' in r.stdout, 'un hôte déclaré sans raison est refusé', r.stdout)
    banc.refuse('un fetch vers api.anthropic.com est refusé avec un message clair',
                ecrire('src/appel.js', "fetch('https://api.anthropic.com/v1/messages')\n"), 'API Anthropic')
    banc.refuse('un appel Python requests.get vers un site est refusé',
                ecrire('src/appel.py', "import requests\n\nrequests.get('https://exemple-api.org/x')\n"), 'exemple-api.org')
    banc.accepte('un lien de navigation <a href="https://…"> n\'est pas un appel réseau',
                 ecrire('src/lien.html', '<a href="https://www.service-public.fr">aide</a>\n'))


def essais_suivi(banc: Banc, chemin_vide: dict) -> None:
    print('\n— Suivi, partage, analyses exigées')
    banc.accepte('un changement de périmètre non validé donne une alerte mais ne bloque pas',
                 lambda q: (q / 'docs' / 'perimetre.md').write_text(lire(q / 'docs' / 'perimetre.md') + '| 13/11/2026 | Export Excel ajouté | non | |\n', encoding='utf-8'),
                 'périmètre')

    def fiche_partage(potentiel: str, cellule: str):
        def modifier(projet: pathlib.Path) -> None:
            substituer('docs/partage.md', r'(?m)^(- Potentiel de réutilisation[^:\n]*:).*$', r'\1 ' + potentiel)(projet)
            substituer('docs/partage.md', r'(?m)^(- Cellule opérationnelle informée[^:\n]*:).*$', r'\1 ' + cellule)(projet)
        return modifier
    banc.accepte('un outil réutilisable non signalé à la cellule donne une alerte amicale, sans bloquer', fiche_partage('oui', ''), 'vélo électrique')
    banc.accepte('la même fiche avec une date d\'information ne déclenche plus l\'alerte', fiche_partage('oui', '12/11/2026'),
                 'cellule opérationnelle a été informée', absent='vélo électrique')
    banc.accepte('un « non » raisonné est accepté sans alerte', fiche_partage('non', 'non, outil propre à notre métier'), absent='vélo électrique')
    banc.accepte('sans outil d\'analyse, le contrôle passe et dit ce qui n\'a pas été testé', lambda q: None, 'non testé', env=chemin_vide)
    banc.refuse('avec --exiger-analyses, un outil d\'analyse absent est refusé', lambda q: None, 'Analyse exigée',
                options=('--exiger-analyses',), env=chemin_vide)

    def poser_module(projet: pathlib.Path) -> None:
        for fichier in ('prise-en-main.js', 'prise-en-main.css'):
            shutil.copy2(SC.parent / 'assets' / 'prise-en-main' / fichier, projet / 'src' / fichier)
    banc.accepte('le module de prise en main fourni passe tous les contrôles', poser_module)


RUSTINE = """# Fiche rustine — demo

Version documentée : 0.1.0

- Problème de fond (une phrase) : la trame de l'agence change chaque année
- À qui il appartient (agence, éditeur d'un logiciel, organisation interne) : agence
- Signalé le (date, à qui, par fonction) : pas encore
- Ce dont l'outil dépend (trames, exports, logiciels, et leurs versions) : trame 2026
- Condition de retrait (ce qui doit changer pour qu'on n'en ait plus besoin) : le logiciel produit lui-même la trame
- Revue avant le (JJ/MM/AAAA) : 01/06/2026
"""
QUESTIONS_IA = """# Questions-tests

Modèle utilisé : modèle local d'essai

| Entrée (inventée) | Ce qu'on attend (vérifiable) | Résultat au dernier passage | Date | Modèle |
|---|---|---|---|---|
| Devis fictif n°1 | trouve les 3 montants | conforme | 10/11/2026 | modèle local |
"""
APPEL_IA = "import requests\n\n\ndef resumer(texte):\n    return requests.post('http://localhost:11434/api/generate', json={'prompt': texte}, timeout=60)\n"


def essais_editeur(banc: Banc, tmp: pathlib.Path) -> None:
    print('\n— Rôle d\'éditeur : contrat d\'entrée, rustine, IA, traçabilité')
    ligne_entree = '| Trame agence | Agence | Trame 2026, colonnes Code station et Date | tests/donnees/trame-2026.csv | nouvelle ligne et nouvel exemple |\n'
    def declarer_entree(avec_exemple: bool):
        def modifier(projet: pathlib.Path) -> None:
            (projet / 'docs' / 'entrees.md').write_text(lire(projet / 'docs' / 'entrees.md') + ligne_entree, encoding='utf-8')
            if avec_exemple:
                ecrire('tests/donnees/trame-2026.csv', 'Code station;Date\nFICTIF01;01/01/2026\n')(projet)
        return modifier
    banc.refuse('livraison : une entrée déclarée sans fichier exemple est refusée', declarer_entree(False), 'fichier exemple absent')
    banc.accepte('brouillon : la même entrée sans exemple ne bloque pas', declarer_entree(False), 'fichier exemple absent', options=('--brouillon',))
    banc.accepte('une entrée avec son exemple est acceptée', declarer_entree(True), 'chacun avec son exemple')
    banc.accepte('un outil qui lit des fichiers sans contrat d\'entrée reçoit une alerte', ecrire('src/lecture.js', 'const r = new FileReader();\n'), 'lit des fichiers')
    projet = banc.accepte('une rustine à revoir et non signalée donne deux alertes, sans bloquer', ecrire('docs/rustine.md', RUSTINE), 'Rustine à réexaminer')
    verifier('pas encore signalé' in fabriquer(projet, '--sans-paquet').stdout and 'Rustine : oui — problème de fond : la trame' in lire(projet / 'dist' / 'fiche-registre.txt'),
             'le problème non signalé est rappelé, la fiche du registre le mentionne')
    banc.refuse('livraison : une fonction d\'IA sans questions-tests est refusée', ecrire('src/coeur/ia.py', APPEL_IA), 'questions-tests')
    banc.accepte('brouillon : la même fonction d\'IA ne bloque pas', ecrire('src/coeur/ia.py', APPEL_IA), 'questions-tests', options=('--brouillon',))
    projet = banc.accepte('une fonction d\'IA avec ses questions-tests récentes est acceptée',
                          lambda q: (ecrire('src/coeur/ia.py', APPEL_IA)(q), ecrire('tests/ia/questions.md', QUESTIONS_IA)(q)), 'rejouées le 2026-11-10')
    verifier('Fonction d\'IA : oui — questions-tests rejouées le 10/11/2026' in lire(projet / 'dist' / 'fiche-registre.txt'), 'la fiche du registre signale la fonction d\'IA')
    banc.accepte('des documents produits sans mention de traçabilité donnent une alerte',
                 ecrire('src/impression.js', 'function imprimer() { window.print(); }\n'), 'sans la mention')
    banc.accepte('avec la brique de traçabilité, la mention est reconnue',
                 ecrire('src/impression.js', 'function imprimer(p) { p.textContent = Tracabilite.produitAvec("Démo", "0.1.0", []); window.print(); }\n'),
                 'mention de traçabilité', absent='sans la mention')
    r = run('creer_projet.py', 'options', '--format', 'A', '--dest', str(tmp), '--rustine', '--ia', '--briques')
    projet = tmp / 'options'
    verifier(r.returncode == 0 and (projet / 'docs' / 'rustine.md').exists() and (projet / 'tests' / 'ia' / 'questions.md').exists()
             and (projet / 'src' / 'briques' / 'tracabilite.js').exists() and not (projet / 'src' / 'briques' / 'test_briques.py').exists(),
             'creer_projet --rustine --ia --briques pose la fiche, les questions-tests et les briques (sans leurs tests)', r.stdout + r.stderr)
    briques = SC.parent / 'assets' / 'briques'
    r = subprocess.run([sys.executable, str(briques / 'test_briques.py')], capture_output=True, text=True, encoding='utf-8', check=False)
    verifier(r.returncode == 0, 'briques Python : tests passés', r.stdout + r.stderr)
    if si_outil('node', 'tests des briques JavaScript'):
        r = subprocess.run(['node', str(briques / 'test_briques.js')], capture_output=True, text=True, encoding='utf-8', check=False)
        verifier(r.returncode == 0, 'briques JavaScript : tests passés', r.stdout + r.stderr)
    shutil.rmtree(briques / '__pycache__', ignore_errors=True)


def nir_a_cle_valide() -> str:
    """Numéro inventé dont la clé est calculée ici : aucun numéro à clé juste n'est écrit dans la skill."""
    corps = '2990475123456'
    return f'{corps} {97 - int(corps) % 97:02d}'


def iban_a_cle_valide() -> str:
    reste = '12345678901234567890123'
    numerique = ''.join(str(int(c, 36)) for c in reste + 'FR00')
    return f'FR{98 - int(numerique) % 97:02d}{reste}'


def essais_audit(banc: Banc, tmp: pathlib.Path) -> None:
    print('\n— Audit : liberté de créer, socle de sûreté, maintien en condition opérationnelle')
    retirer = lambda relatif: (lambda projet: (projet / relatif).unlink())   # noqa: E731
    # liberté : ce qui est de la complétude n'arrête pas un brouillon
    banc.accepte('brouillon : un document absent n\'arrête pas la création', retirer('docs/recette.md'), 'Document absent', options=('--brouillon',))
    banc.refuse('livraison : le même document absent est réclamé', retirer('docs/recette.md'), 'Document absent')
    banc.accepte('brouillon : une dépendance non figée est signalée sans bloquer', ecrire('requirements.txt', 'flask\n'), 'Dépendances non figées', options=('--brouillon',))
    # sûreté : jamais allégée, même en brouillon
    banc.refuse('brouillon : un fichier de sûreté absent reste bloquant', retirer('.gitignore'), 'Fichier obligatoire absent', options=('--brouillon',))
    nir, iban = nir_a_cle_valide(), iban_a_cle_valide()
    projet = banc.refuse('brouillon : un numéro de sécurité sociale à clé valide est refusé',
                         ecrire('tests/donnees/beneficiaires.csv', f'nom;numero\nPersonne fictive;{nir}\n'), 'numéro de sécurité sociale à clé valide', options=('--brouillon',))
    verifier(nir not in lire(projet / 'dist' / 'bilan-fabrication.md') and nir.replace(' ', '') not in lire(projet / 'dist' / 'bilan-fabrication.md'),
             'le numéro n\'est pas recopié dans le bilan')
    banc.refuse('brouillon : un IBAN à clé valide est refusé', ecrire('docs/exemple.md', f'Virement vers {iban}\n'), 'IBAN à clé valide', options=('--brouillon',))
    banc.accepte('un numéro dont un chiffre est changé (clé fausse) est accepté', ecrire('tests/donnees/beneficiaires.csv', f'numero\n{nir[:-1]}{(int(nir[-1]) + 1) % 10}\n'),
                 'Aucun numéro de sécurité sociale ni IBAN')
    banc.accepte('un exemple à clé valide déclaré fictif est accepté, avec une alerte',
                 lambda q: (ecrire('tests/donnees/rib.csv', f'iban\n{iban}\n')(q), ecrire('tests/donnees/exemples-fictifs.txt', f'# exemples inventés\n{iban}\n')(q)),
                 'déclaré(s) fictif(s)')
    banc.accepte('une lecture XML sans analyseur réglé donne un rappel', ecrire('src/lecture.py', 'from lxml import etree\n\n\ndef lire(chemin):\n    return etree.parse(chemin)\n'), 'lecture XML')
    banc.accepte('des saisies gardées dans le navigateur sans export sont signalées',
                 ecrire('src/saisie.js', 'function garder(v) { localStorage.setItem("brouillon-demo", v); }\n'), 'sans fonction d\'export')
    # maintien en condition opérationnelle : classes
    classe1 = substituer('README.md', r'(?m)^Classe : .*$', 'Classe : 1 (essentiel)')
    banc.accepte('classe 1 sans mode dégradé : signalé en brouillon', classe1, 'mode-degrade.md absent', options=('--brouillon',))
    banc.refuse('classe 1 sans mode dégradé : refusé à la livraison', classe1, 'mode-degrade.md absent')
    def classe1_complete(q: pathlib.Path) -> None:
        classe1(q)
        ecrire('docs/mode-degrade.md', '# Mode dégradé\n\nVersion documentée : 0.1.0\n\n- Ce que font les agents : ils utilisent le dernier export.\n')(q)
        substituer('docs/fiche-dsi.md', r'(?m)^(\s*-\s*Dernier essai de restauration[^:\n]*:).*$', r'\1 01/10/2026, réussi')(q)
    projet = banc.accepte('classe 1 avec mode dégradé et restauration récente : accepté', classe1_complete, 'Classe 1 : mode dégradé écrit')
    verifier('Classe : 1 (essentiel) · mode dégradé : écrit' in lire(projet / 'dist' / 'fiche-registre.txt')
             and 'Contrôle : fabriquer.py' in lire(projet / 'dist' / 'bilan-fabrication.md') and '(contrôle ' in lire(projet / 'dist' / 'fiche-registre.txt'),
             'la fiche du registre donne la classe et le mode dégradé ; la version du contrôle est tracée')
    r = run('creer_projet.py', 'essentiel', '--format', 'B', '--dest', str(tmp), '--classe', '1', '--image', 'nginx:1.27.3')
    verifier(r.returncode == 0 and 'Classe : 1 (proposée' in lire(tmp / 'essentiel' / 'README.md') and (tmp / 'essentiel' / 'docs' / 'mode-degrade.md').exists(),
             'creer_projet --classe 1 propose la classe et pose la page du mode dégradé', r.stdout + r.stderr)
    r = run('creer_projet.py', 'fichier-vital', '--format', 'A', '--niveau', 'partage', '--dest', str(tmp), '--classe', '1')
    r = fabriquer(tmp / 'fichier-vital', '--brouillon', '--sans-paquet')
    verifier(r.returncode != 0 and 'le niveau durable est nécessaire' in r.stdout, 'classe 1 au niveau partagé : refusé, même en brouillon', r.stdout[-400:])


def essais_format_a(tmp: pathlib.Path) -> None:
    print('\n— Format A')
    r = run('creer_projet.py', 'demo-a', '--format', 'A', '--dest', str(tmp))
    projet = tmp / 'demo-a'
    verifier(r.returncode == 0 and not (projet / 'deploy').exists(), 'projet A créé sans dossier deploy/', r.stdout + r.stderr)
    completer(projet)
    r = fabriquer(projet)
    verifier(r.returncode == 0 and bool(list((projet / 'dist').glob('*.zip'))), 'projet A correct accepté et empaqueté', r.stdout + r.stderr)


def essais_niveaux(tmp: pathlib.Path) -> None:
    print('\n— Liberté d\'abord : niveau partagé, brouillon, dossier de transmission')
    r = run('creer_projet.py', 'leger', '--format', 'A', '--niveau', 'partage', '--dest', str(tmp))
    leger = tmp / 'leger'
    verifier(r.returncode == 0 and (leger / 'docs' / 'partage.md').exists() and not (leger / 'docs' / 'recette.md').exists()
             and not (leger / 'deploy').exists(), 'niveau partagé : dossier léger (partage.md, pas de recette ni de deploy)', r.stdout + r.stderr)
    r = run('creer_projet.py', 'x1', '--format', 'B', '--niveau', 'partage', '--dest', str(tmp))
    verifier(r.returncode != 0 and 'format A' in (r.stdout + r.stderr), 'le niveau partagé est refusé pour un outil sur serveur')
    r = fabriquer(leger)
    verifier(r.returncode == 0 and 'aucun point bloquant' in r.stdout, 'un projet partagé vierge ne bloque pas l\'agent (que des recommandations)', r.stdout)
    verifier('Format : fichier HTML autonome · niveau partagé' in lire(leger / 'dist' / 'fiche-registre.txt')
             and 'Où le trouver : à compléter' in lire(leger / 'dist' / 'fiche-registre.txt'), 'fiche du registre d\'un outil partagé : format et manques affichés')
    dossier = leger / 'dist' / 'dossier-transmission.md'
    verifier(dossier.exists() and 'Utilisable par des collègues' in lire(dossier), 'le dossier de transmission est écrit, avec son statut')
    banc = Banc(pathlib.Path(shutil.copytree(leger, tmp / 'base-leger', ignore=shutil.ignore_patterns('dist'))), tmp / 'travail-leger')
    banc.refuse('niveau partagé : un mot de passe en dur reste refusé', ecrire('src/page.js', 'const password = "abcdef123";\n'), 'écrit en dur')
    banc.refuse('niveau partagé : une bibliothèque chargée depuis un CDN reste refusée',
                ecrire('src/page.html', '<script src="https://cdn.exemple-externe.org/x.js"></script>\n'), 'cdn.exemple-externe.org')
    banc.refuse('niveau partagé : eval() reste refusé', ecrire('src/page.js', 'function f(x) { return eval(x); }\n'), 'eval()')
    banc.refuse('niveau partagé : un test qui échoue reste bloquant',
                ecrire('tests/test_somme.py', 'def test_somme():\n    assert 1 + 1 == 3\n'), 'Tests en échec')
    banc.accepte('niveau partagé : un test qui passe est exécuté', ecrire('tests/test_somme.py', 'def test_somme():\n    assert 1 + 1 == 2\n'),
                 'Tests exécutés')
    banc.refuse('niveau partagé sur un autre format que A : refusé', remplacer('README.md', 'Format : A', 'Format : B'), 'format A')
    banc.accepte('demande d\'installation en niveau partagé : on propose le niveau durable',
                 substituer('docs/partage.md', r"(?m)^(- Demande d'installation[^:\n]*:).*$", r'\1 oui'), 'niveau durable')

    print('\n— Brouillon : travailler librement, sans paquet transmissible')
    r = run('creer_projet.py', 'brouillon', '--format', 'B', '--titre', 'Brouillon', '--dest', str(tmp), '--image', 'nginx:1.27.3')
    projet = tmp / 'brouillon'
    r = fabriquer(projet, '--brouillon')
    verifier(r.returncode == 0 and 'Brouillon : pas encore transmissible' in r.stdout,
             'un brouillon durable vierge ne bloque pas l\'agent mais n\'est pas déclaré transmissible', r.stdout)
    verifier('_brouillon.zip' in r.stdout, 'le paquet est nommé « brouillon »')
    r = fabriquer(projet)
    verifier(r.returncode == 1 and 'À retravailler avant installation' in lire(projet / 'dist' / 'dossier-transmission.md'),
             'sans --brouillon, le même projet est « à retravailler » et le dossier le dit')
    completer(projet)
    r = fabriquer(projet)
    verifier(r.returncode == 0 and 'Installable avec réserves' in lire(projet / 'dist' / 'dossier-transmission.md'),
             'un projet durable complet est « installable avec réserves » tant que l\'essai de restauration manque')
    substituer('docs/fiche-dsi.md', r'(?m)^(- Dernier essai de restauration[^:\n]*:).*$', r'\1 02/11/2026')(projet)
    substituer('docs/partage.md', r'(?m)^(- Potentiel de réutilisation[^:\n]*:).*$', r'\1 non')(projet)
    r = fabriquer(projet)
    verifier('Statut : Prêt à installer' in r.stdout or 'Statut : Installable avec réserves' in r.stdout,
             'le statut est affiché à l\'écran', r.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as dossier:
        tmp = pathlib.Path(dossier)
        (tmp / 'chemin-vide').mkdir()
        chemin_vide = {'PATH': str(tmp / 'chemin-vide')}                 # simule un poste sans aucun outil d'analyse
        projet = essais_creation(tmp)
        essais_projet_vierge_puis_complet(projet)
        base = pathlib.Path(shutil.copytree(projet, tmp / 'base', ignore=shutil.ignore_patterns('dist')))
        banc = Banc(base, tmp)
        essais_tests(banc)
        essais_code(banc)
        essais_dependances(banc, chemin_vide)
        essais_socle(banc)
        essais_reseau(banc)
        essais_suivi(banc, chemin_vide)
        essais_editeur(banc, tmp)
        essais_audit(banc, tmp)
        essais_format_a(tmp)
        essais_niveaux(tmp)
    if sautes:
        print(f'\n{len(sautes)} cas sauté(s) faute d\'outil : ' + ' ; '.join(sautes))
    print('\nRÉSULTAT :', 'tout est bon' if not echecs else f'{len(echecs)} point(s) à corriger')
    return 0 if not echecs else 1


if __name__ == '__main__':
    sys.exit(main())
