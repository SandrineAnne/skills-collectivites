"""Autotest de la skill entretien-outils : chaque script fait ce qu'il promet, et rien de plus.

Usage : python3 autotest_entretien.py [--fabrique CHEMIN]
Crée des outils fictifs dans un dossier temporaire (avec la skill fabrique-outils, cherchée à côté de celle-ci),
puis vérifie : passage de version partout à la fois, relevé sans modification ni fuite de secret, remise à niveau
sans rien écraser, revue des outils, et que build/fabriquer.py accepte le résultat. Code de sortie 0 si tout est bon.
"""
from __future__ import annotations

import argparse
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

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

ICI = pathlib.Path(__file__).resolve().parent
DATE = '2026-11-13'
echecs: list[str] = []

ANCIEN_HTML = '''<!doctype html><html><head><meta charset="utf-8"><title>Vieil outil</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script>/*! jQuery v3.6.0 | (c) OpenJS Foundation */ var j = 1;</script></head>
<body><a href="https://www.service-public.fr">aide</a>
<script>fetch('https://api.exemple-externe.org/donnees'); var champs = ['date_naissance', 'montant'];</script></body></html>
'''
ANCIEN_PY = 'from flask import Flask\npassword = "Zx9pLm22qq"\napp = Flask(__name__)\n'
HTML_PROPRE = '''<!doctype html><html><head><meta charset="utf-8"><title>Outil propre</title></head>
<body><p id="r"></p><script>
// RG-01 : le total est la somme des montants
function total(lignes) { return lignes.reduce((a, b) => a + b, 0); }
document.getElementById('r').textContent = String(total([1, 2]));
</script></body></html>
'''


def verifier(condition: bool, libelle: str, detail: str = '') -> None:
    print(('  ✓ ' if condition else '  ✗ ') + libelle)
    if not condition:
        echecs.append(libelle)
        if detail:
            print('      ' + detail.strip().replace('\n', '\n      ')[:1500])


def lancer(script: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding='utf-8', errors='replace',
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, check=False)


def empreinte(dossier: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted(dossier.rglob('*')):
        if p.is_file():
            h.update(p.relative_to(dossier).as_posix().encode() + p.read_bytes())
    return h.hexdigest()


def lire(p: pathlib.Path) -> str:
    return p.read_text(encoding='utf-8')


def trouver_fabrique(option: str | None) -> pathlib.Path:
    for candidat in ([pathlib.Path(option)] if option else [
            pathlib.Path(os.environ.get('FABRIQUE_OUTILS', '/nonexistent')), ICI.parent.parent / 'fabrique-outils',
            pathlib.Path('/mnt/skills/plugins/fabrique-outils'), pathlib.Path('/mnt/skills/user/fabrique-outils')]):
        if (candidat / 'scripts' / 'creer_projet.py').exists():
            return candidat.resolve()
    sys.exit('Arrêt : skill fabrique-outils introuvable (option --fabrique).')


def charger(chemin: pathlib.Path, nom: str):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module


class Banc:
    def __init__(self, fabrique: pathlib.Path, tmp: pathlib.Path):
        self.fabrique, self.tmp = fabrique, tmp
        self.completer = charger(fabrique / 'scripts' / 'autotest_fabrique.py', 'autotest_fabrique_ref').completer

    def projet(self, nom: str, fmt: str = 'B', dossier: pathlib.Path | None = None) -> pathlib.Path:
        dest = dossier or self.tmp
        r = lancer(self.fabrique / 'scripts' / 'creer_projet.py', nom, '--format', fmt, '--titre', nom.capitalize(), '--dest', str(dest),
                   '--image', 'nginx:1.27.3')
        if r.returncode != 0:
            sys.exit('Arrêt : création du projet d\'essai impossible.\n' + r.stdout + r.stderr)
        self.completer(dest / nom)
        return dest / nom

    def fabriquer(self, projet: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
        return lancer(projet / 'build' / 'fabriquer.py', str(projet), '--date', DATE, '--sans-paquet', *args)


# ---------------------------------------------------------------- nouvelle_version.py
def essais_version(banc: Banc) -> None:
    print('\n— Passage de version (nouvelle_version.py)')
    script = ICI / 'nouvelle_version.py'
    p = banc.projet('versions')
    verifier(banc.fabriquer(p).returncode == 0, 'le projet d\'essai passe le contrôle avant tout changement')
    avant = empreinte(p)
    r = lancer(script, str(p), 'correction', 'Libellé du total corrigé', '--simulation', '--date', DATE)
    verifier(r.returncode == 0 and empreinte(p) == avant and 'SIMULATION' in r.stdout, '--simulation montre sans rien écrire', r.stdout + r.stderr)
    r = lancer(script, str(p), 'correction', 'Libellé du total corrigé', '--date', DATE)
    compose, deploiement = lire(p / 'deploy' / 'compose.yaml'), lire(p / 'deploy' / 'playbook_deploy.yaml')
    verifier(r.returncode == 0 and lire(p / 'VERSION').strip() == '0.1.1', 'correction : 0.1.0 → 0.1.1', r.stdout + r.stderr)
    verifier("APP_VERSION = '0.1.1'" in lire(p / 'src' / 'coeur' / 'regles.py') and 'Version : 0.1.1' in lire(p / 'README.md')
             and 'Version documentée : 0.1.1' in lire(p / 'docs' / 'composants.md'), 'version changée dans le code, le README et les documents')
    verifier('outil.version: "0.1.1"' in compose and 'app_version: "0.1.1"' in deploiement and 'nginx:1.27.3' in compose,
             'version changée dans le déploiement, sans toucher aux versions des images')
    changelog = lire(p / 'CHANGELOG.md')
    verifier(re.search(r'(?m)^## \[0\.1\.1\] — 2026-11-13\n### Corrigé\n- Libellé du total corrigé', changelog) is not None
             and changelog.index('[0.1.1]') < changelog.index('[0.1.0]'), 'entrée « Corrigé » ajoutée en tête du CHANGELOG')
    r = banc.fabriquer(p)
    verifier(r.returncode == 0, 'après la correction, fabriquer.py accepte le projet (versions alignées partout)', r.stdout)
    r = lancer(script, str(p), 'evolution', 'Export des totaux', '--date', DATE)
    verifier(lire(p / 'VERSION').strip() == '0.2.0' and re.search(r'(?m)^# SPEC.*v0\.2', lire(p / 'SPEC.md')) is not None,
             'évolution : 0.1.1 → 0.2.0, numéro de la SPEC suivi', r.stdout)
    verifier(banc.fabriquer(p).returncode == 0, 'après l\'évolution, fabriquer.py accepte toujours le projet')
    r = lancer(script, str(p), 'majeure', 'Nouveau format de sauvegarde', '--date', DATE)
    verifier(lire(p / 'VERSION').strip() == '1.0.0' and '### Modifié' in lire(p / 'CHANGELOG.md'), 'majeure : 0.2.0 → 1.0.0, rubrique « Modifié »')
    readme = lire(p / 'README.md').replace('Version : 1.0.0', 'Version : 9.9.9')
    (p / 'README.md').write_text(readme, encoding='utf-8')
    r = lancer(script, str(p), 'correction', 'Essai', '--date', DATE)
    verifier('Version : 9.9.9' in lire(p / 'README.md') and '9.9.9' in r.stdout and 'non modifié' in r.stdout,
             'une autre version écrite ailleurs est signalée, jamais modifiée', r.stdout)
    (p / 'VERSION').write_text('v1\n', encoding='utf-8')
    verifier(lancer(script, str(p), 'correction', 'Essai').returncode != 0, 'un fichier VERSION invalide arrête tout')
    (p / 'VERSION').unlink()
    r = lancer(script, str(p), 'correction', 'Essai')
    verifier(r.returncode != 0 and 'remettre_a_niveau' in (r.stdout + r.stderr), 'sans fichier VERSION : renvoi vers la remise à niveau')


# ---------------------------------------------------------------- releve_outil.py
def essais_releve(tmp: pathlib.Path) -> None:
    print('\n— Relevé d\'un outil existant (releve_outil.py)')
    ancien = tmp / 'ancien-outil'
    ancien.mkdir()
    (ancien / 'index.html').write_text(ANCIEN_HTML, encoding='utf-8')
    (ancien / 'app.py').write_text(ANCIEN_PY, encoding='utf-8')
    (ancien / 'requirements.txt').write_text('flask\nrequests==2.31.0\n', encoding='utf-8')
    avant = empreinte(ancien)
    sortie = tmp / 'releve.md'
    r = lancer(ICI / 'releve_outil.py', str(ancien), '--sortie', str(sortie))
    texte = lire(sortie) if sortie.exists() else ''
    verifier(r.returncode == 0 and empreinte(ancien) == avant, 'le relevé ne modifie rien dans l\'outil', r.stdout + r.stderr)
    verifier('Format probable : **B**' in texte, 'format probable reconnu (code serveur Flask)')
    verifier('| leaflet | 1.9.4 |' in texte and '| jQuery | 3.6.0 |' in texte and '| requests | 2.31.0 |' in texte,
             'bibliothèques repérées avec leur version (chargée, embarquée, déclarée)')
    verifier('api.exemple-externe.org' in texte.split('## Ressources chargées depuis Internet')[1].split('Simples mentions')[0],
             'appel externe classé en « chargement »')
    verifier('www.service-public.fr' in texte.split('Simples mentions')[1].split('\n')[0], 'simple lien classé en « mention »')
    verifier('Zx9pLm22qq' not in texte and 'Zx••••••' in texte, 'secret repéré, valeur masquée (aucune fuite dans le relevé)')
    verifier('flask (requirements.txt)' in texte.split('## Dépendances non figées')[1].split('##')[0], 'dépendance non figée repérée')
    verifier('« date_naissance »' in texte, 'donnée de personne possible repérée')
    verifier('Manquant : README.md' in texte, 'éléments de dossier manquants listés')


# ---------------------------------------------------------------- remettre_a_niveau.py
def essais_remise(banc: Banc, tmp: pathlib.Path) -> None:
    print('\n— Remise à niveau sans rien écraser (remettre_a_niveau.py)')
    script = ICI / 'remettre_a_niveau.py'
    copie = tmp / 'vieil-outil'
    copie.mkdir()
    (copie / 'index.html').write_text(HTML_PROPRE, encoding='utf-8')
    (copie / 'README.md').write_text('# Mon vieil outil\n\nTexte d\'origine, à garder.\n', encoding='utf-8')
    (copie / 'CHANGELOG.md').write_text('# Historique maison\n\n- 2024 : première mise en service.\n', encoding='utf-8')
    html_avant = (copie / 'index.html').read_bytes()
    commun = ('--format', 'A', '--titre', 'Vieil outil', '--date', DATE, '--fabrique', str(banc.fabrique))
    r = lancer(script, str(copie), *commun)
    verifier(r.returncode != 0 and not (copie / 'VERSION').exists(), 'sans --copie : arrêt, rien n\'est créé', r.stdout + r.stderr)
    r = lancer(script, str(copie), '--copie', '--format', 'B', '--niveau', 'partage', '--fabrique', str(banc.fabrique))
    verifier(r.returncode != 0, 'niveau partagé refusé pour un format B')
    r = lancer(script, str(copie), '--copie', *commun)
    readme, changelog = lire(copie / 'README.md'), lire(copie / 'CHANGELOG.md')
    verifier(r.returncode == 0 and (copie / 'index.html').read_bytes() == html_avant, 'remise à niveau faite, code de l\'outil intact', r.stdout + r.stderr)
    verifier("Texte d'origine, à garder." in readme and re.search(r'^# Mon vieil outil\n\nVersion : 1\.0\.0\nFormat : A\nNiveau : durable', readme, re.M) is not None,
             'README existant conservé, lignes Version, Format et Niveau ajoutées en tête')
    verifier('première mise en service' in changelog and '## [1.0.0] — 2026-11-13' in changelog, 'CHANGELOG existant conservé, entrée 1.0.0 ajoutée')
    attendus = ['SPEC.md', 'VERSION', 'docs/incidents.md', 'docs/composants.md', 'docs/partage.md', '.gitignore', 'tests/LISEZMOI.md']
    verifier(all((copie / f).exists() for f in attendus) and 'déduite du code' in lire(copie / 'SPEC.md'), 'dossier manquant créé (SPEC reconstituée, incidents, partage…)')
    verifier((copie / 'build' / 'fabriquer.py').read_bytes() == (banc.fabrique / 'scripts' / 'fabriquer.py').read_bytes()
             and '"index.html"' in lire(copie / 'build' / 'controles.json'), 'contrôle copié, code laissé en place et déclaré')
    avant = empreinte(copie)
    r = lancer(script, str(copie), '--copie', *commun)
    verifier(r.returncode == 0 and empreinte(copie) == avant and 'Créés (0)' in r.stdout, 'relancée, la remise à niveau ne change rien')
    r = banc.fabriquer(copie, '--brouillon')
    verifier(r.returncode == 0 and 'Brouillon' in r.stdout, 'en brouillon, l\'outil repris ne bloque pas (dossier à compléter)', r.stdout)
    r = banc.fabriquer(copie)
    verifier(r.returncode == 1 and 'À retravailler' in lire(copie / 'dist' / 'dossier-transmission.md'), 'pour une livraison, le dossier dit « à retravailler »')
    spec = re.sub(r'(?m)^- RG-01 — .*$', '- RG-01 — Le total est la somme des montants (déduite du code, à confirmer par le métier).', lire(copie / 'SPEC.md'), count=1)
    (copie / 'SPEC.md').write_text(spec, encoding='utf-8')
    (copie / 'tests' / 'test_total.py').write_text('# RG-01 : test de caractérisation (comportement actuel)\ndef test_rg01():\n    assert 1 + 2 == 3\n', encoding='utf-8')
    r = banc.fabriquer(copie, '--brouillon')
    verifier('chacune a un test et une mention dans le code' in r.stdout, 'la règle citée dans le code laissé en place (index.html) est bien trouvée', r.stdout)
    fabriquer_copie = copie / 'build' / 'fabriquer.py'
    fabriquer_copie.write_text(lire(fabriquer_copie) + '\n# modification locale\n', encoding='utf-8')
    r = lancer(script, str(copie), '--copie', *commun)
    verifier('diffère' in r.stdout and 'modification locale' in lire(fabriquer_copie), 'un fabriquer.py différent est signalé, pas remplacé')
    r = lancer(script, str(copie), '--copie', '--rustine', '--briques', *commun)
    verifier((copie / 'docs' / 'rustine.md').exists() and (copie / 'src' / 'briques' / 'entrees.py').exists(),
             'reprise : fiche rustine et briques communes ajoutées sur demande', r.stdout + r.stderr)
    r = lancer(script, str(copie), '--copie', '--mettre-a-jour-fabriquer', *commun)
    verifier((copie / 'build' / 'fabriquer.py.ancien').exists() and 'modification locale' not in lire(fabriquer_copie),
             'avec --mettre-a-jour-fabriquer : remplacé, l\'ancien est gardé')


# ---------------------------------------------------------------- veille_outils.py
def essais_veille(banc: Banc, tmp: pathlib.Path) -> None:
    print('\n— Revue des outils (veille_outils.py)')
    script = ICI / 'veille_outils.py'
    parc = tmp / 'outils'
    parc.mkdir()
    sain = banc.projet('sain', dossier=parc)
    restauration = r'(?m)^(- Dernier essai de restauration[^:\n]*:).*$'
    (sain / 'docs' / 'fiche-dsi.md').write_text(re.sub(restauration, r'\1 02/11/2026', lire(sain / 'docs' / 'fiche-dsi.md')), encoding='utf-8')
    perime = banc.projet('perime', dossier=parc)
    (perime / 'docs' / 'composants.md').write_text(lire(perime / 'docs' / 'composants.md').replace('2027-06', '2026-06'), encoding='utf-8')
    incident = banc.projet('incident', dossier=parc)
    with (incident / 'docs' / 'incidents.md').open('a', encoding='utf-8') as journal:
        journal.write('| 12/11/2026 | gênant | Export vide | à chercher | | | ouvert |\n')
    sortie = tmp / 'revue.md'
    r = lancer(script, str(parc), '--date', DATE, '--sortie', str(sortie))
    texte = lire(sortie) if sortie.exists() else ''
    maintenant = texte.split('## À traiter maintenant')[1].split('## À planifier')[0] if '## À planifier' in texte else ''
    verifier(r.returncode == 1 and '3 outil(s) examiné(s)' in texte, 'trois outils trouvés ; code de sortie 1 s\'il y a quelque chose à traiter', r.stdout + r.stderr)
    verifier('Perime' in maintenant and 'support terminé depuis le 2026-06-30' in maintenant, 'composant sans support : à traiter maintenant')
    verifier('Incident' in maintenant and 'incident ouvert du 12/11/2026' in maintenant, 'incident ouvert : à traiter maintenant')
    verifier('- Sain (v0.1.0, classe 2)' in texte.split('## En ordre')[1], 'outil en règle : en ordre, avec sa classe')
    vital = banc.projet('vital', dossier=parc)
    (vital / 'README.md').write_text(re.sub(r'(?m)^Classe : .*$', 'Classe : 1 (essentiel)', lire(vital / 'README.md')), encoding='utf-8')
    ancien = banc.projet('ancien-controle', dossier=parc)
    controle = ancien / 'build' / 'fabriquer.py'
    controle.write_text(re.sub(r"(?m)^VERSION_CONTROLE = '[0-9.]+'", "VERSION_CONTROLE = '0.9'", lire(controle)), encoding='utf-8')
    sans_classe = banc.projet('sans-classe', dossier=parc)
    (sans_classe / 'README.md').write_text(re.sub(r'(?m)^Classe : .*$', 'Classe : à fixer', lire(sans_classe / 'README.md')), encoding='utf-8')
    abandonne = banc.projet('abandonne', dossier=parc)
    (abandonne / 'docs' / 'composants.md').write_text(
        lire(abandonne / 'docs' / 'composants.md').replace('2027-06', 'non maintenu depuis 2023'), encoding='utf-8')
    r = lancer(script, str(parc), '--date', DATE)
    verifier('non maintenu depuis 2023' in r.stdout.split('## À planifier')[0],
             'composant noté « non maintenu » : à traiter maintenant', r.stdout)
    verifier('classe 1 : mode dégradé à écrire' in r.stdout and 'contrôle embarqué ancien (0.9' in r.stdout and 'classe non fixée' in r.stdout,
             'revue : classe 1 sans mode dégradé, contrôle embarqué ancien et outil sans classe signalés', r.stdout)
    verifier('restauration' in texte.split('## À planifier')[1] or 'restauration' in maintenant, 'essai de restauration manquant rappelé pour les autres')
    r = lancer(script, str(parc), '--date', DATE, '--chercher', 'nginx')
    verifier(all(n in r.stdout.split('## À traiter')[0] for n in ('sain', 'perime', 'incident')), '--chercher nginx retrouve les outils qui l\'utilisent')
    r = lancer(script, str(parc), '--date', DATE, '--controler')
    verifier('contrôle en échec' in r.stdout.split('## À planifier')[0] and r.returncode == 1, '--controler lance le contrôle de chaque outil', r.stdout)
    r = banc.fabriquer(incident)
    verifier('Incident encore ouvert' in r.stdout, 'fabriquer.py signale aussi l\'incident ouvert')
    rustine = banc.projet('rustine', dossier=parc)
    (rustine / 'docs' / 'rustine.md').write_text('# Fiche rustine\n\nVersion documentée : 0.1.0\n\n- Problème de fond : trame qui change\n'
                                                '- Revue avant le (JJ/MM/AAAA) : 01/06/2026\n', encoding='utf-8')
    (rustine / 'tests' / 'ia').mkdir(parents=True, exist_ok=True)
    (rustine / 'tests' / 'ia' / 'questions.md').write_text('| Entrée | Attendu | Résultat | Date | Modèle |\n|---|---|---|---|---|\n'
                                                          '| Devis fictif | 3 montants | conforme | 01/09/2025 | local |\n', encoding='utf-8')
    r = lancer(script, str(parc), '--date', DATE)
    planifier = r.stdout.split('## À planifier')[1].split('## En ordre')[0] if '## À planifier' in r.stdout else ''
    verifier('rustine à réexaminer (revue prévue le 2026-06-01)' in planifier and 'questions-tests de la fonction d\'IA à rejouer' in planifier
             and 'dont 1 rustine(s)' in r.stdout and 'remonter au processus' in r.stdout,
             'revue : rustine à réexaminer, questions-tests d\'IA à rejouer, décision du parc rappelée', r.stdout)
    vide = tmp / 'vide'
    vide.mkdir()
    verifier(lancer(script, str(vide)).returncode not in (0, 1), 'un dossier sans outil est signalé clairement')


def main() -> int:
    analyseur = argparse.ArgumentParser(prog='autotest_entretien.py')
    analyseur.add_argument('--fabrique', help='chemin de la skill fabrique-outils')
    options = analyseur.parse_args()
    fabrique = trouver_fabrique(options.fabrique)
    with tempfile.TemporaryDirectory() as dossier:
        tmp = pathlib.Path(dossier)
        banc = Banc(fabrique, tmp)
        essais_version(banc)
        essais_releve(tmp)
        essais_remise(banc, tmp)
        essais_veille(banc, tmp)
    shutil.rmtree(ICI / '__pycache__', ignore_errors=True)
    print('\nRÉSULTAT :', 'tout est bon' if not echecs else f'{len(echecs)} point(s) à corriger')
    return 0 if not echecs else 1


if __name__ == '__main__':
    sys.exit(main())
