"""Shared fixtures for vault/collection tests."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ADS_LIBRARIES = [
    {'id': 'lib-jades', 'name': 'JADES', 'num_documents': 2},
    {'id': 'lib-lesnes', 'name': 'LESNeS', 'num_documents': 1},
    {'id': 'lib-dm', 'name': 'dark matter', 'num_documents': 2},
    {'id': 'lib-mega', 'name': 'MEGALIB', 'num_documents': 4},
]

# bibcode -> (ads_key, record)
PAPERS = {
    '2020ApJ...aaa': (
        'ARTICLE{Alpha2020ApJ',
        {'title': '{Alpha}', 'year': '2020', 'keywords': '{galaxies}'},
    ),
    '2021MNRAS.bbb': (
        'ARTICLE{Beta2021MNRAS',
        {'title': '{Beta}', 'year': '2021', 'keywords': '{surveys}'},
    ),
    '2022ApJ...ccc': (
        'ARTICLE{Gamma2022ApJ',
        {'title': '{Gamma}', 'year': '2022', 'keywords': '{cosmology}'},
    ),
    '2023ApJ...ddd': (
        'ARTICLE{Delta2023ApJ',
        {'title': '{Delta}', 'year': '2023', 'keywords': '{galaxies}'},
    ),
}

LIBRARY_BIBCODES = {
    'lib-jades': ['2020ApJ...aaa', '2023ApJ...ddd'],
    'lib-lesnes': ['2021MNRAS.bbb'],
    'lib-dm': ['2022ApJ...ccc', '2023ApJ...ddd'],
    'lib-mega': ['2020ApJ...aaa', '2021MNRAS.bbb', '2022ApJ...ccc', '2023ApJ...ddd'],
}


def fake_get_library(library_id, num_documents, config):
    return list(LIBRARY_BIBCODES[library_id])


def fake_export_bibcodes(bibcodes, headers, **kwargs):
    out = {}
    for bibcode in bibcodes:
        ads_key, rec = PAPERS[bibcode]
        out[ads_key] = dict(rec)
    return out


def collection_bibs(vault_root):
    coll = Path(vault_root) / 'bib' / 'collections'
    if not coll.is_dir():
        return []
    return sorted(p.name for p in coll.iterdir() if p.suffix == '.bib')
