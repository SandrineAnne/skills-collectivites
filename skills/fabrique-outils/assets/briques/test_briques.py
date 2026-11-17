"""Tests des briques Python (lancés par autotest_fabrique.py)."""
import datetime
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import entrees  # noqa: E402
import tracabilite  # noqa: E402

VERSIONS = {'Trame 2026': ['Code station', 'Date du bilan', 'Débit entrée'], 'Trame 2025': ['Code station', 'Date', 'Débit']}


def test_trame_reconnue_malgre_accents_et_espaces():
    assert entrees.reconnaitre_version(['code  STATION', 'Date du bilan', 'Debit entree', 'Autre'], VERSIONS) == 'Trame 2026'


def test_trame_inconnue_message_clair():
    try:
        entrees.reconnaitre_version(['Code station', 'Date du bilan'], VERSIONS)
    except ValueError as erreur:
        assert 'Trame 2026' in str(erreur) and 'Débit entrée' in str(erreur) and 'référent' in str(erreur)
    else:
        raise AssertionError('une trame incomplète aurait dû être refusée')


def test_mention_de_tracabilite():
    with tempfile.TemporaryDirectory() as dossier:
        source = pathlib.Path(dossier) / 'trame.xlsx'
        source.write_bytes(b'contenu fictif')
        mention = tracabilite.produit_avec('bilan réglementaire', '1.2.0', [source], datetime.date(2026, 11, 15))
        assert mention.startswith('Produit avec bilan réglementaire v1.2.0 le 15/11/2026 à partir de : trame.xlsx (')
        assert len(tracabilite.empreinte(source)) == 8
    assert tracabilite.produit_avec('X', '1.0.0', [], datetime.date(2026, 1, 2)).endswith('saisie manuelle')


if __name__ == '__main__':
    for nom, fonction in sorted(globals().items()):
        if nom.startswith('test_'):
            fonction()
    print('briques Python : tout est bon')
