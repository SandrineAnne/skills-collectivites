"""Brique commune « traçabilité » — version 1.0.0.

À copier telle quelle dans src/briques/ ; une évolution se propose à la cellule opérationnelle.
Ajoute à tout document produit la mention :
« Produit avec <outil> v<version> le <date> à partir de : <fichiers sources (empreinte)> ».
"""
from __future__ import annotations

import datetime
import hashlib
import pathlib

VERSION = '1.0.0'


def empreinte(chemin: str | pathlib.Path) -> str:
    """Empreinte courte (8 caractères) d'un fichier source."""
    condense = hashlib.sha256()
    with open(chemin, 'rb') as fichier:
        for bloc in iter(lambda: fichier.read(1 << 16), b''):
            condense.update(bloc)
    return condense.hexdigest()[:8]


def produit_avec(outil: str, version: str, sources: list[str | pathlib.Path] = (), date: datetime.date | None = None) -> str:
    """Mention à placer en pied de chaque document produit."""
    jour = (date or datetime.date.today()).strftime('%d/%m/%Y')
    liste = ', '.join(f'{pathlib.Path(s).name} ({empreinte(s)})' for s in sources)
    return f'Produit avec {outil} v{version} le {jour} à partir de : {liste or "saisie manuelle"}'
