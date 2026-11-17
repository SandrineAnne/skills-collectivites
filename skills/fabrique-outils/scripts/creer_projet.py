"""Crée le dossier d'un nouvel outil à partir des gabarits de la skill.

Usage : python3 creer_projet.py <nom-court> --format A|B|C|D [--niveau partage|durable] [--titre "Nom affiché"]
                                [--dest .] [--port 8150] [--image nginx:1.27.3]

  nom-court   lettres minuscules, chiffres et tirets (ex. renommage-dsu) : sert de nom de dossier,
              de dossier serveur (/data/apps/<nom>) et d'adresse (<nom>.exemple.fr)
  --format    A HTML autonome · B web conteneurisé · C bureau (MSI) · D Grist
  --niveau    durable (défaut) : outil destiné à être installé, socle complet
              partage : un fichier HTML pour des collègues, dossier léger (format A seulement) ; on peut passer
              au niveau durable à tout moment, sans rien perdre
  --port      (format B) port local publié sur 127.0.0.1
  --image     (format B) image de départ, avec une version précise

Le projet créé contient aussi une copie de fabriquer.py (build/) : il se contrôle sans Claude.
Un dossier existant n'est jamais écrasé. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import pathlib
import re
import shutil
import sys

for _flux in (sys.stdout, sys.stderr):          # consoles Windows : toujours écrire en UTF-8
    with contextlib.suppress(AttributeError, ValueError):
        _flux.reconfigure(encoding='utf-8', errors='replace')

RACINE_SKILL = pathlib.Path(__file__).resolve().parent.parent
GABARITS = RACINE_SKILL / 'assets' / 'gabarits'
OPTIONS = RACINE_SKILL / 'assets' / 'gabarits-options'
BRIQUES = RACINE_SKILL / 'assets' / 'briques'
VERSION_DEPART = '0.1.0'
NOMS_SPECIAUX = {'gitignore': '.gitignore', 'env.exemple': 'deploy/.env.exemple'}
FICHIERS_PARTAGE = {'README.md', 'CHANGELOG.md', 'gitignore', 'reseau-autorise.txt', 'docs/partage.md'}
CIBLES_OPTIONS = {'rustine': ('rustine.md', 'docs/rustine.md'), 'ia': ('questions-ia.md', 'tests/ia/questions.md'),
                  'degrade': ('mode-degrade.md', 'docs/mode-degrade.md')}
LIGNE_CLASSE = 'Classe : À COMPLÉTER (1 essentiel, 2 important, 3 confort ; fixée par la cellule opérationnelle)'
SPEC_COURTE = """> À COMPLÉTER : cinq lignes suffisent. Supprimer cette ligne ensuite.

# SPEC — {titre} — v0.1

Statut : brouillon

- Besoin (une phrase, avec les mots du métier) : À COMPLÉTER
- Qui l'utilisera, à quelle fréquence : À COMPLÉTER
- Données : aucune donnée de personne (sinon : passer au niveau durable)
- Appels vers l'extérieur : aucun (sinon : les déclarer dans reseau-autorise.txt, avec la raison)
- Hors périmètre : À COMPLÉTER

## Règles de gestion (facultatif ; recommandé dès qu'il y a un calcul ou un tri)
- RG-01 — <une règle = une phrase vérifiable, avec un exemple chiffré>
"""
AIDE_SRC = ('Les règles métier vont ici, sans interface (cœur pur : pas de fichier, pas de réseau, pas d\'écran).\n'
            'Chaque règle porte son identifiant dans un commentaire (RG-01…).\n'
            'La version de l\'application se déclare une seule fois : APP_VERSION = \'0.1.0\' (valeur du fichier VERSION).\n')
AIDE_TESTS = ('Un test au moins par règle de gestion, sur des exemples inventés, avec le résultat attendu écrit à l\'avance.\n'
              'Les tests sont des fonctions « test_… » dans des fichiers test_*.py (ou *.test.js) : fabriquer.py les exécute.\n'
              'Le nom de la règle (RG-01…) figure dans le test. Un défaut corrigé = un test ajouté.\n')
PROCHAINES_ETAPES_PARTAGE = """Prochaines étapes :
  1. Écrire les cinq lignes de SPEC.md avec l'agent, puis construire l'outil (un seul fichier HTML, bibliothèques embarquées).
  2. Lancer : python3 build/fabriquer.py     (socle de sûreté : secrets, appels externes, code dangereux ; le reste est une recommandation)
  3. Si d'autres veulent l'installer ou le reprendre : passer en « Niveau : durable » dans README.md, la skill complète le dossier."""
PROCHAINES_ETAPES = """Prochaines étapes :
  1. Remplir SPEC.md avec la cellule opérationnelle, puis la faire valider (jalon 1).
  2. Construire l'outil dans src/ ; chaque règle (RG-xx) a un test dans tests/.
  3. Lancer : python3 build/fabriquer.py --brouillon     (contrôle d'étape : tests exécutés, sans exigence de complétude)
  4. À la livraison : python3 build/fabriquer.py          (refuse de fabriquer le paquet si quelque chose ne colle pas)"""


def nom_court(valeur: str) -> str:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,40}', valeur):
        raise argparse.ArgumentTypeError('lettres minuscules, chiffres et tirets seulement (2 à 41 caractères)')
    return valeur


def port_local(valeur: str) -> str:
    if not valeur.isdigit() or not 1024 <= int(valeur) <= 65535:
        raise argparse.ArgumentTypeError('nombre entre 1024 et 65535')
    return valeur


def lire_options(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(prog='creer_projet.py', description='Crée le dossier d\'un nouvel outil.')
    analyseur.add_argument('nom', type=nom_court, help='nom court : minuscules, chiffres, tirets')
    analyseur.add_argument('--format', required=True, type=str.upper, choices=['A', 'B', 'C', 'D'],
                           help='A : un simple fichier ; B : application web sur serveur ; C : application de bureau ; D : tableau Grist')
    analyseur.add_argument('--niveau', default='durable', choices=['durable', 'partage', 'partagé'],
                           help='durable (outil à installer, défaut) ou partage (un fichier HTML pour des collègues, format A)')
    analyseur.add_argument('--rustine', action='store_true', help='l\'outil contourne un logiciel, une trame ou un processus : ajoute la fiche rustine')
    analyseur.add_argument('--ia', action='store_true', help='l\'outil utilise une IA à l\'usage : ajoute les questions-tests')
    analyseur.add_argument('--briques', action='store_true', help='copie les briques communes (traçabilité, reconnaître une trame) dans src/briques/')
    analyseur.add_argument('--classe', type=int, choices=(1, 2, 3), help='ce que coûte une panne : 1 essentiel (chaque jour, ou remplace un logiciel), '
                           '2 important, 3 confort ; la classe 1 ajoute la page du mode dégradé')
    analyseur.add_argument('--titre', help='nom affiché de l\'outil')
    analyseur.add_argument('--dest', default='.', help='dossier où créer le projet')
    analyseur.add_argument('--port', type=port_local, default='8150', help='(format B) port local')
    analyseur.add_argument('--image', default='À-COMPLÉTER:0.0.0', help='(format B) image de départ, avec sa version')
    return analyseur.parse_args(argv)


def spec_depuis_modele(titre: str) -> str:
    """Reprend le bloc ```markdown de references/modele-spec.md : une seule source de vérité pour la SPEC."""
    modele = (RACINE_SKILL / 'references' / 'modele-spec.md').read_text(encoding='utf-8')
    bloc = re.search(r'```markdown\n(.*?)\n```', modele, re.S)
    if not bloc:
        sys.exit('Arrêt : le modèle de SPEC est introuvable dans references/modele-spec.md')
    spec = bloc.group(1).replace('<Nom de l\'application>', titre).replace('v<x.y>', 'v0.1')
    spec = re.sub(r'(?m)^Statut : .*$', 'Statut : brouillon', spec, count=1)
    spec = re.sub(r'(?m)^- RG-02 — …\n', '', spec)
    return '> À COMPLÉTER : remplir chaque section, puis supprimer cette ligne.\n\n' + spec


def ecrire(chemin: pathlib.Path, texte: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding='utf-8')


def cible_du_gabarit(relatif: pathlib.Path, nom: str) -> str:
    if relatif.name in NOMS_SPECIAUX:
        return NOMS_SPECIAUX[relatif.name]
    if relatif.name == 'vhost.conf':
        return f'deploy/{nom}.conf'
    return relatif.as_posix()


def gabarit_retenu(relatif: pathlib.Path, valeurs: dict[str, str]) -> bool:
    """Le dossier léger du niveau partagé ne reprend que les gabarits essentiels ; le serveur n'a de gabarits qu'en format B."""
    if valeurs['NIVEAU'] == 'partagé':
        return relatif.as_posix() in FICHIERS_PARTAGE
    return not (relatif.parts[0] == 'deploy' and valeurs['FORMAT'] != 'B')


def poser_gabarits(dest: pathlib.Path, valeurs: dict[str, str]) -> None:
    for gabarit in sorted(GABARITS.rglob('*')):
        relatif = gabarit.relative_to(GABARITS)
        if not gabarit.is_file() or not gabarit_retenu(relatif, valeurs):
            continue
        texte = gabarit.read_text(encoding='utf-8')
        for cle, valeur in valeurs.items():
            texte = texte.replace('{{' + cle + '}}', valeur)
        ecrire(dest / cible_du_gabarit(relatif, valeurs['NOM']), texte)


def poser_options(dest: pathlib.Path, valeurs: dict[str, str], rustine: bool, ia: bool, briques: bool, classe: int | None = None) -> list[str]:
    """Fiche rustine, questions-tests d'IA et briques communes : seulement quand l'outil en a besoin. Rien n'est écrasé."""
    poses = []
    for cle, voulu in (('rustine', rustine), ('ia', ia), ('degrade', classe == 1)):
        source, cible = CIBLES_OPTIONS[cle]
        if voulu and not (dest / cible).exists():
            texte = (OPTIONS / source).read_text(encoding='utf-8')
            for nom, valeur in valeurs.items():
                texte = texte.replace('{{' + nom + '}}', valeur)
            ecrire(dest / cible, texte)
            poses.append(cible)
    readme = dest / 'README.md'
    if classe and readme.exists() and LIGNE_CLASSE in readme.read_text(encoding='utf-8'):
        readme.write_text(readme.read_text(encoding='utf-8').replace(
            LIGNE_CLASSE, f'Classe : {classe} (proposée ; à confirmer par la cellule opérationnelle)'), encoding='utf-8')
        poses.append(f'classe {classe} proposée')
    if briques:
        for brique in sorted(BRIQUES.glob('*')):
            if brique.is_file() and not brique.name.startswith('test_') and not (dest / 'src' / 'briques' / brique.name).exists():
                (dest / 'src' / 'briques').mkdir(parents=True, exist_ok=True)
                shutil.copy2(brique, dest / 'src' / 'briques' / brique.name)
                poses.append(f'src/briques/{brique.name}')
    return poses


def main(argv: list[str]) -> int:
    options = lire_options(argv)
    partage = options.niveau.startswith('partag')
    if partage and options.format != 'A':
        sys.exit('Arrêt : le niveau partagé ne convient qu\'au format A (un simple fichier). '
                 'Un outil sur serveur, sur poste ou dans Grist est durable : retirer --niveau partage.')
    dest = pathlib.Path(options.dest).resolve() / options.nom
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f'Arrêt : {dest} existe déjà et n\'est pas vide. Rien n\'a été modifié.')
    valeurs = {'NOM': options.nom, 'TITRE': options.titre or options.nom, 'VERSION': VERSION_DEPART, 'FORMAT': options.format,
               'NIVEAU': 'partagé' if partage else 'durable', 'DATE': datetime.date.today().isoformat(), 'PORT': options.port, 'PORT_INTERNE': '80', 'IMAGE': options.image,
               'DOMAINE': f'{options.nom}.exemple.fr',
               'OU_TROUVER': f'https://{options.nom}.exemple.fr' if options.format == 'B' else 'À COMPLÉTER'}
    poser_gabarits(dest, valeurs)
    ecrire(dest / 'SPEC.md', SPEC_COURTE.format(titre=valeurs['TITRE']) if partage else spec_depuis_modele(valeurs['TITRE']))
    ecrire(dest / 'VERSION', VERSION_DEPART + '\n')
    ecrire(dest / 'src' / 'coeur' / 'LISEZMOI.md', AIDE_SRC)
    ecrire(dest / 'tests' / 'LISEZMOI.md', AIDE_TESTS)
    (dest / 'build').mkdir(exist_ok=True)
    shutil.copy2(RACINE_SKILL / 'scripts' / 'fabriquer.py', dest / 'build' / 'fabriquer.py')
    poses = poser_options(dest, valeurs, options.rustine, options.ia, options.briques, options.classe)
    if poses:
        print('Ajouts selon le besoin : ' + ', '.join(poses))
    print(f'Projet créé : {dest} (niveau {valeurs["NIVEAU"]})\n\n{PROCHAINES_ETAPES_PARTAGE if partage else PROCHAINES_ETAPES}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
