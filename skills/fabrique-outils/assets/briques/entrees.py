"""Brique commune « reconnaître une trame » — version 1.0.0.

À copier telle quelle dans src/briques/ ; une évolution se propose à la cellule opérationnelle.
Pour un outil qui lit des fichiers produits par d'autres (trame d'une agence, export d'un logiciel) :
reconnaît la version du format à partir des colonnes, ou dit clairement ce qui manque.
"""
from __future__ import annotations

import unicodedata

VERSION = '1.0.0'


def normaliser(texte: str) -> str:
    sans_accents = ''.join(c for c in unicodedata.normalize('NFD', str(texte or '')) if unicodedata.category(c) != 'Mn')
    return ' '.join(sans_accents.lower().split())


def reconnaitre_version(colonnes: list[str], versions: dict[str, list[str]]) -> str:
    """Nom de la version reconnue ; ValueError avec un message clair sinon."""
    presentes = {normaliser(c) for c in colonnes}
    proche: tuple[str, list[str]] | None = None
    for nom, attendues in versions.items():
        manquantes = [c for c in attendues if normaliser(c) not in presentes]
        if not manquantes:
            return nom
        if proche is None or len(manquantes) < len(proche[1]):
            proche = (nom, manquantes)
    detail = f' Version la plus proche : {proche[0]} ; il manque : {", ".join(proche[1])}.' if proche else ''
    raise ValueError(f'Format de fichier non reconnu.{detail} Si la trame a changé, prévenez le référent de l\'outil : '
                     'il faut ajouter cette nouvelle version.')
