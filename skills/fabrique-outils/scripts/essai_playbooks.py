"""Essai à blanc des playbooks de déploiement et de contrôle, sans serveur ni conteneur.

Usage : python3 essai_playbooks.py        (Linux ; nécessite ansible-core : pip install ansible-core)

Crée un projet de format B dans un dossier temporaire, remplace Podman et Docker par un faux moteur qui répond
ce qu'on lui demande, sert une fausse adresse de santé sur 127.0.0.1, puis joue les deux playbooks sur la machine
locale. Vérifie qu'ils réussissent avec Podman et avec Docker, et qu'ils échouent quand ils le doivent
(image « latest », redémarrage automatique absent, .env trop ouvert, mauvaise version, moteur inconnu).
Cet essai ne remplace pas le premier déploiement sur le serveur de test : il évite d'y découvrir une faute de syntaxe.
Code de sortie 0 si tout est bon.
"""
from __future__ import annotations

import contextlib
import http.server
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

SC = pathlib.Path(__file__).resolve().parent
FAUX_NGINX = """#!/bin/sh
# Faux nginx : note chaque appel ; FAUX_NGINX_RC est son code de sortie (0 par défaut).
echo "$*" >> "$FAUX_NGINX"
exit "${FAUX_NGINX_RC:-0}"
"""
FAUX_MOTEUR = """#!/bin/sh
# Faux moteur de conteneurs : répond aux seules questions posées par les playbooks.
case "$*" in
  *State.Status*) echo running ;;
  *State.Health*)                          # FAUX_SANTE : état de santé (vide = pas de vérification de santé)
    if [ -n "$FAUX_DEMARRAGE" ] && [ ! -e "$FAUX_DEMARRAGE" ]; then : > "$FAUX_DEMARRAGE"; echo starting
    else printf '%s\\n' "${FAUX_SANTE-healthy}"; fi ;;
  *RestartPolicy*) echo "${FAUX_RESTART:-always}" ;;
  *Config.Image*) echo "${FAUX_IMAGE:-docker.io/library/nginx:1.27.3}" ;;
  tag*) echo "$*" >> "$FAUX_ETIQUETTES" ;;
  compose*) echo "$0 $*" >> "$FAUX_JOURNAL" ;;
  *) echo "appel inattendu : $*" >&2; exit 3 ;;
esac
"""
echecs: list[str] = []


def verifier(condition: bool, libelle: str, detail: str = '') -> None:
    print(('  ✓ ' if condition else '  ✗ ') + libelle)
    if not condition:
        echecs.append(libelle)
        print('      ' + detail.strip().replace('\n', '\n      ')[-1200:])


def port_libre() -> int:
    with socket.socket() as prise:
        prise.bind(('127.0.0.1', 0))
        return prise.getsockname()[1]


class Sante(http.server.BaseHTTPRequestHandler):
    """Répond 200 sur /sante avec le numéro de version, comme le ferait l'application."""

    def do_GET(self) -> None:
        corps = b'{"etat": "ok", "version": "0.1.0"}'
        self.send_response(200 if self.path == '/sante' else 404)
        self.send_header('Content-Length', str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args) -> None:              # silence : la sortie reste lisible
        pass


def preparer(tmp: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, dict[str, str]]:
    """Projet, dossier d'application et environnement avec le faux moteur en tête du chemin."""
    creation = subprocess.run([sys.executable, str(SC / 'creer_projet.py'), 'demo', '--format', 'B', '--dest', str(tmp),
                               '--image', 'nginx:1.27.3'], capture_output=True, text=True, check=False)
    if creation.returncode != 0:
        sys.exit('Arrêt : création du projet d\'essai impossible.\n' + creation.stderr)
    faux, appli = tmp / 'faux', tmp / 'appli'
    faux.mkdir()
    appli.mkdir()
    for nom in ('podman', 'docker'):
        (faux / nom).write_text(FAUX_MOTEUR, encoding='utf-8')
    (faux / 'nginx').write_text(FAUX_NGINX, encoding='utf-8')
    for outil in faux.iterdir():
        outil.chmod(0o755)
    (appli / '.env').write_text('APP_SECRET=essai\n', encoding='utf-8')
    (appli / '.env').chmod(0o600)
    env = {**os.environ, 'PATH': f'{faux}{os.pathsep}{os.environ["PATH"]}', 'FAUX_JOURNAL': str(tmp / 'journal.txt'),
           'FAUX_ETIQUETTES': str(tmp / 'etiquettes.txt'), 'FAUX_NGINX': str(tmp / 'nginx.txt'), 'FAUX_DEMARRAGE': '',
           'ANSIBLE_NOCOLOR': '1', 'ANSIBLE_LOCALHOST_WARNING': 'False'}
    return tmp / 'demo' / 'deploy', appli, env


def jouer(playbook: pathlib.Path, appli: pathlib.Path, port: int, env: dict[str, str], *variables: str) -> subprocess.CompletedProcess:
    commande = ['ansible-playbook', '-i', 'localhost,', '-c', 'local', '-e', 'cible=localhost', '-e', 'ansible_become=false',
                '-e', f'app_dir={appli}', '-e', f'port_local={port}']
    for variable in variables:
        commande += ['-e', variable]
    return subprocess.run([*commande, str(playbook)], capture_output=True, text=True, env=env, check=False)


def essais(deploy: pathlib.Path, appli: pathlib.Path, port: int, env: dict[str, str]) -> None:
    deploiement, controle = deploy / 'playbook_deploy.yaml', deploy / 'playbook_check.yaml'
    for moteur in ('podman', 'docker'):
        print(f'\n— Moteur {moteur}')
        r = jouer(deploiement, appli, port, env, f'moteur={moteur}')
        journal = pathlib.Path(env['FAUX_JOURNAL']).read_text(encoding='utf-8') if pathlib.Path(env['FAUX_JOURNAL']).exists() else ''
        verifier(r.returncode == 0 and f'{moteur} compose up -d' in journal, 'déploiement réussi, « compose up -d » lancé avec le bon moteur', r.stdout)
        verifier((appli / 'compose.yaml').exists() and (appli / 'demo.conf').exists(), 'fichiers de déploiement posés dans le dossier de l\'application')
        r = jouer(controle, appli, port, env, f'moteur={moteur}', 'verifier_version=true')
        verifier(r.returncode == 0, 'contrôle réussi, version en service vérifiée', r.stdout)
    print('\n— Pannes provoquées : le contrôle doit échouer')
    pannes = (('une image « latest » est refusée', {'FAUX_IMAGE': 'nginx:latest'}, ()),
              ('un redémarrage automatique absent est refusé', {'FAUX_RESTART': 'no'}, ()),
              ('une version en service différente est refusée', {}, ('verifier_version=true', 'version_attendue=9.9.9')))
    for libelle, env_plus, variables in pannes:
        r = jouer(controle, appli, port, {**env, **env_plus}, *variables)
        verifier(r.returncode != 0, libelle, r.stdout)
    (appli / '.env').chmod(0o644)
    verifier(jouer(controle, appli, port, env).returncode != 0, 'un fichier .env lisible par tous est refusé')
    verifier(jouer(deploiement, appli, port, env).returncode != 0, 'le déploiement s\'arrête si .env est trop ouvert')
    (appli / '.env').chmod(0o600)
    verifier(jouer(deploiement, appli, port, env, 'moteur=lxc').returncode != 0, 'un moteur inconnu est refusé')
    essais_sante(controle, appli, port, env)
    essais_etiquette(deploiement, appli, port, env)
    essais_nginx(deploiement, appli, port, env)


def vider(env: dict[str, str], *cles: str) -> None:
    """Efface les notes du faux moteur et du faux nginx avant un essai."""
    for cle in cles:
        pathlib.Path(env[cle]).write_text('', encoding='utf-8')


def lignes(env: dict[str, str], cle: str) -> list[str]:
    return pathlib.Path(env[cle]).read_text(encoding='utf-8').splitlines()


def essais_sante(controle: pathlib.Path, appli: pathlib.Path, port: int, env: dict[str, str]) -> None:
    print('\n— État de santé du conteneur')
    r = jouer(controle, appli, port, {**env, 'FAUX_SANTE': 'unhealthy'})
    verifier(r.returncode != 0 and 'pas en bonne santé' in r.stdout, 'un conteneur « unhealthy » fait échouer le contrôle, avec un message clair', r.stdout)
    r = jouer(controle, appli, port, {**env, 'FAUX_SANTE': ''})
    verifier(r.returncode == 0 and 'ne définit pas de vérification de santé' in r.stdout,
             'un conteneur sans vérification de santé passe, et le contrôle le dit', r.stdout)
    with tempfile.TemporaryDirectory() as dossier:
        r = jouer(controle, appli, port, {**env, 'FAUX_DEMARRAGE': str(pathlib.Path(dossier) / 'deja-demande')})
    verifier(r.returncode == 0 and r.stdout.count('FAILED - RETRYING') == 1,
             'un conteneur encore en démarrage (« starting ») est attendu, puis accepté', r.stdout)


def essais_etiquette(deploiement: pathlib.Path, appli: pathlib.Path, port: int, env: dict[str, str]) -> None:
    print('\n— Étiquette de retour arrière « avant-maj » (le compose.yaml du projet d\'essai lance nginx:1.27.3)')
    empreinte = 'sha256:' + 'ab12' * 16
    cas = (('une version précédente reçoit l\'étiquette avant-maj', 'nginx:1.26.0', ['tag nginx:1.26.0 nginx:avant-maj']),
           ('un registre avec port garde son port : registre.exemple.fr:5000/app:1.0', 'registre.exemple.fr:5000/app:1.0',
            ['tag registre.exemple.fr:5000/app:1.0 registre.exemple.fr:5000/app:avant-maj']),
           ('une image désignée par son empreinte ne fait pas échouer le déploiement', f'depot/app@{empreinte}',
            [f'tag depot/app@{empreinte} depot/app:avant-maj']),
           ('rejouer la même version ne déplace pas l\'étiquette', 'nginx:1.27.3', []),
           ('ni quand le moteur rend son nom complet (Podman)', 'docker.io/library/nginx:1.27.3', []),
           ('une image déjà étiquetée avant-maj n\'est pas re-étiquetée', 'nginx:avant-maj', []))
    for libelle, image, attendu in cas:
        vider(env, 'FAUX_ETIQUETTES')
        r = jouer(deploiement, appli, port, {**env, 'FAUX_IMAGE': image})
        verifier(r.returncode == 0 and lignes(env, 'FAUX_ETIQUETTES') == attendu, libelle,
                 f'étiquettes posées : {lignes(env, "FAUX_ETIQUETTES")}\n{r.stdout}')


def essais_nginx(deploiement: pathlib.Path, appli: pathlib.Path, port: int, env: dict[str, str]) -> None:
    print('\n— nginx')
    vhosts = appli / 'vhosts'
    vhosts.mkdir()
    options = ('deploy_vhost=true', f'vhost_dir={vhosts}')
    vider(env, 'FAUX_NGINX')
    r = jouer(deploiement, appli, port, env)
    verifier(r.returncode == 0 and lignes(env, 'FAUX_NGINX') == [] and not list(vhosts.glob('*.conf')),
             'sans vhost à poser, nginx n\'est pas appelé', r.stdout)
    r = jouer(deploiement, appli, port, env, *options)
    verifier(r.returncode == 0 and len(list(vhosts.glob('*.conf'))) == 1 and lignes(env, 'FAUX_NGINX') == ['-t', '-s reload'],
             'vhost posé : la configuration est testée, puis nginx est rechargé', f'appels à nginx : {lignes(env, "FAUX_NGINX")}\n{r.stdout}')
    vider(env, 'FAUX_NGINX')
    r = jouer(deploiement, appli, port, env, *options)
    verifier(r.returncode == 0 and lignes(env, 'FAUX_NGINX') == ['-t'], 'vhost inchangé : testé, mais nginx n\'est pas rechargé',
             f'appels à nginx : {lignes(env, "FAUX_NGINX")}\n{r.stdout}')
    for fichier in vhosts.glob('*.conf'):
        fichier.unlink()
    vider(env, 'FAUX_NGINX')
    r = jouer(deploiement, appli, port, {**env, 'FAUX_NGINX_RC': '1'}, *options)
    verifier(r.returncode != 0 and 'PAS été rechargé' in r.stdout and '-s reload' not in lignes(env, 'FAUX_NGINX'),
             'configuration nginx refusée : le playbook s\'arrête sans recharger, et le dit', f'appels à nginx : {lignes(env, "FAUX_NGINX")}\n{r.stdout}')


def main() -> int:
    if os.name == 'nt' or not shutil.which('ansible-playbook'):
        print('Essai non fait : il faut Linux et ansible-core (pip install ansible-core).')
        return 2
    port = port_libre()
    serveur = http.server.ThreadingHTTPServer(('127.0.0.1', port), Sante)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory() as dossier:
            deploy, appli, env = preparer(pathlib.Path(dossier))
            essais(deploy, appli, port, env)
    finally:
        serveur.shutdown()
    print('\nRÉSULTAT :', 'tout est bon' if not echecs else f'{len(echecs)} point(s) à corriger')
    return 0 if not echecs else 1


if __name__ == '__main__':
    sys.exit(main())
