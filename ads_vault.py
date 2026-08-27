# Export ADS libraries into an Obsidian vault: paper notes, collection .bib files,
# optional arXiv PDFs, and a project subset for Overleaf.
import argparse
import os
import requests
from ads_lib import (
    ads_auth_headers,
    get_library,
    select_libraries,
    slug_library_name,
    export_bibcodes,
    dict_to_bib,
    citekey_from_ads_key,
    safe_note_stem,
    record_catalogue,
    strip_bib_braces,
    write_paper_note,
    download_arxiv_pdf,
    filter_records,
    records_from_export_csv,
    reclean_papers_dir,
    get_ads_token,
)

######### Parameters #########
# Default vault folder if --vault and ADS_VAULT are unset
vault_root = 'example_vault'
# Leave empty to export all libraries, or comma-separated ADS library names
library_name = ''
# Skip the union library so it is not treated as a collection
skip_libraries = 'MEGALIB'
export_format = 'bibtexabs'
bibtex_keyformat = '%1H%R'
sort_format = 'first_author asc'
fix_journal = True
# Download arXiv PDFs into pdfs/{citekey}.pdf when missing (never overwrites)
fetch_pdfs = False
# Same tagging as ads_tag_per_lib.py → YAML `tags`
add_keyword = True
keep_only_myads_tags = False
tag_prefix = ''
# Overleaf subset: write projects/<project_name>/refs.bib
project_name = 'example'
# Empty = all exported citekeys; or comma-separated citekeys; or an ADS library slug
project_citekeys = ''
project_collection = ''
# If ADS auth is missing, optionally build the vault from a previous CSV export
offline_csv = ''
offline_collection = 'offline-export'
######################################

VAULT_DIRS = (
    'papers',
    'pdfs',
    'extracts',
    os.path.join('bib', 'collections'),
    'projects',
    'templates',
    '.obsidian',
)

HOME_NOTE = """# Literature

ADS is the catalogue. This vault is the reading and writing layer: one note per paper, local PDFs, and BibTeX for Overleaf.

Requires Obsidian 1.9+ with the **Bases** core plugin enabled (Settings → Core plugins → Bases). **PDF++** is recommended for annotating files in `pdfs/`.

## Papers

![[papers.base]]

Use the view tabs on the table: **Reading list**, **Unread**, and **By collection**. You can edit `read_status` and `relevance` in the table. `tags` come from ADS libraries (same rule as `ads_tag_per_lib.py`) plus keyword tags.

## Collections

Paper notes use `collections` from your ADS library names. Filter in the base with `collections.contains("your-library-slug")`.

Generated BibTeX:

- `bib/library.bib` — union of exported libraries
- `bib/collections/<library>.bib` — one file per ADS library
- `projects/example/refs.bib` — Overleaf subset (defaults to the full export)

Refresh from the repo root:

```bash
source .venv/bin/activate
python ads_vault.py --vault /path/to/this/vault
```
"""

PAPERS_BASE = """filters:
  and:
    - file.inFolder("papers")
    - file.ext == "md"
properties:
  citekey:
    displayName: Citekey
  year:
    displayName: Year
  journal:
    displayName: Journal
  read_status:
    displayName: Read
  relevance:
    displayName: Relevance
  collections:
    displayName: Collections
  tags:
    displayName: Tags
  pdf:
    displayName: PDF
views:
  - type: table
    name: Reading list
    order:
      - file.name
      - year
      - journal
      - read_status
      - collections
      - tags
      - citekey
      - pdf
    sort:
      - property: year
        direction: DESC
  - type: table
    name: Unread
    filters:
      and:
        - 'read_status == "unread"'
    order:
      - file.name
      - year
      - journal
      - collections
      - tags
      - citekey
    sort:
      - property: year
        direction: DESC
  - type: table
    name: By collection
    groupBy:
      property: collections
      direction: ASC
    order:
      - file.name
      - year
      - journal
      - read_status
      - tags
      - citekey
    sort:
      - property: year
        direction: DESC
"""

PAPER_TEMPLATE = """---
citekey:
title:
year:
author:
journal:
doi:
eprint:
adsurl:
keywords:
collections: []
tags: []
read_status: unread
relevance:
pdf:
---
<!-- ads-abstract -->

<!-- ads-body -->
## Summary

## Argument

## Methods

## Figures

## Quotes
"""

OBSIDIAN_TEMPLATES_JSON = """{
  "templatesFolder": "templates"
}
"""

OBSIDIAN_COMMUNITY_PLUGINS = """[]
"""

OBSIDIAN_CORE_PLUGINS = """{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "outgoing-link": true,
  "tag-pane": true,
  "properties": true,
  "page-preview": true,
  "templates": true,
  "command-palette": true,
  "word-count": true,
  "outline": true,
  "bases": true
}
"""


def _write_if_missing(path, content):
    if os.path.exists(path):
        return False
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fout:
        fout.write(content)
    return True


def ensure_vault_layout(root):
    for rel in VAULT_DIRS:
        os.makedirs(os.path.join(root, rel), exist_ok=True)
    _write_if_missing(os.path.join(root, 'pdfs', '.gitkeep'), '')
    _write_if_missing(os.path.join(root, 'extracts', '.gitkeep'), '')
    _write_if_missing(os.path.join(root, 'Home.md'), HOME_NOTE)
    _write_if_missing(os.path.join(root, 'papers.base'), PAPERS_BASE)
    _write_if_missing(os.path.join(root, 'templates', 'paper.md'), PAPER_TEMPLATE)
    _write_if_missing(
        os.path.join(root, '.obsidian', 'templates.json'), OBSIDIAN_TEMPLATES_JSON
    )
    _write_if_missing(
        os.path.join(root, '.obsidian', 'core-plugins.json'),
        OBSIDIAN_CORE_PLUGINS,
    )
    _write_if_missing(
        os.path.join(root, '.obsidian', 'community-plugins.json'),
        OBSIDIAN_COMMUNITY_PLUGINS,
    )


def resolve_vault_root(cli_path=None):
    """CLI --vault, then ADS_VAULT, then vault_root. Expand ~."""
    path = cli_path or os.environ.get('ADS_VAULT') or vault_root
    return os.path.abspath(os.path.expanduser(path.strip()))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export ADS libraries into an Obsidian vault.'
    )
    parser.add_argument(
        '--vault',
        metavar='PATH',
        help='Vault directory (overrides ADS_VAULT and the vault_root default)',
    )
    parser.add_argument(
        '--library',
        action='append',
        dest='libraries',
        metavar='NAME',
        help='ADS library to export. Repeat for several, or comma-separate. '
             'Default: all except skip_libraries.',
    )
    parser.add_argument(
        '--fetch-pdfs',
        action='store_true',
        help='Download missing arXiv PDFs into pdfs/{citekey}.pdf (never overwrites)',
    )
    parser.add_argument(
        '--reclean',
        action='store_true',
        help='Rewrite existing paper notes with cleaned titles/authors/abstracts; skip ADS fetch',
    )
    parser.add_argument(
        '--tag-prefix',
        default=None,
        metavar='PREFIX',
        help='Prefix for ADS library tags (overrides tag_prefix in the script)',
    )
    parser.add_argument(
        '--library-tags-only',
        action='store_true',
        help='YAML tags are only ADS library names (same as keep_only_myads_tags)',
    )
    return parser.parse_args()


def resolve_library_name(cli_libraries=None):
    """CLI --library list, else library_name (comma-separated, empty = all)."""
    if cli_libraries:
        names = []
        for item in cli_libraries:
            names.extend(part.strip() for part in item.split(',') if part.strip())
        return ','.join(names)
    return library_name


def write_bib(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fout:
        dict_to_bib(records, fout)


def token_available():
    try:
        get_ads_token()
        return True
    except FileNotFoundError:
        return False


def load_from_ads(selected_libraries=''):
    headers = ads_auth_headers()
    base_url = 'https://api.adsabs.harvard.edu/v1/biblib'
    config = {'headers': headers, 'url': base_url}
    response = requests.get(base_url + '/libraries', headers=headers)
    all_libraries = response.json()['libraries']
    skip = [name.strip() for name in skip_libraries.split(',') if name.strip()]
    my_libraries = select_libraries(
        all_libraries, selected_libraries, skip_names=skip
    )
    print(f'Exporting {len(my_libraries)} libraries from ADS')
    library_records = {}
    all_records = {}
    collections_by_key = {}
    for library in my_libraries:
        slug = slug_library_name(library['name'])
        bibs = get_library(library['id'], library['num_documents'], config)
        print(f'{slug} has {len(bibs)} bibcodes')
        recs = export_bibcodes(
            bibs,
            headers,
            export_format=export_format,
            keyformat=bibtex_keyformat,
            sort_format=sort_format,
            fix_journal=fix_journal,
        )
        library_records[slug] = recs
        for ads_key, rec in recs.items():
            collections_by_key.setdefault(ads_key, [])
            if slug not in collections_by_key[ads_key]:
                collections_by_key[ads_key].append(slug)
            if ads_key not in all_records:
                all_records[ads_key] = rec
    return library_records, all_records, collections_by_key


def load_from_csv(path, collection):
    recs = records_from_export_csv(path)
    collections_by_key = {key: [collection] for key in recs}
    print(f'Loaded {len(recs)} records from {path} as collection {collection}')
    return {collection: recs}, recs, collections_by_key


def main(cli_vault=None, cli_libraries=None, fetch_pdfs_flag=False,
         reclean_only=False, tag_prefix_cli=None, library_tags_only=False):
    root = resolve_vault_root(cli_vault)
    ensure_vault_layout(root)
    if reclean_only:
        n = reclean_papers_dir(os.path.join(root, 'papers'))
        print(f'Recleaned {n} paper notes in {root}')
        return
    selected = resolve_library_name(cli_libraries)

    csv_path = offline_csv.strip()
    if token_available():
        library_records, all_records, collections_by_key = load_from_ads(selected)
    elif csv_path:
        library_records, all_records, collections_by_key = load_from_csv(
            csv_path, slug_library_name(offline_collection)
        )
    else:
        raise FileNotFoundError(
            "Set ADS_API_TOKEN or mysecrets, or set offline_csv to a previous export."
        )

    for slug, recs in library_records.items():
        write_bib(os.path.join(root, 'bib', 'collections', slug + '.bib'), recs)
    write_bib(os.path.join(root, 'bib', 'library.bib'), all_records)
    print(f'{len(all_records)} unique records into {root}')

    created = updated = pdfs = 0
    papers_dir = os.path.join(root, 'papers')
    pdfs_dir = os.path.join(root, 'pdfs')

    for ads_key, rec in all_records.items():
        citekey = citekey_from_ads_key(ads_key)
        stem = safe_note_stem(citekey)
        note_path = os.path.join(papers_dir, stem + '.md')
        pdf_path = os.path.join(pdfs_dir, stem + '.pdf')
        if fetch_pdfs_flag or fetch_pdfs:
            try:
                if download_arxiv_pdf(rec.get('eprint', ''), pdf_path):
                    pdfs += 1
            except Exception as exc:
                print(f'PDF skip {citekey}: {exc}')
        catalogue = record_catalogue(
            ads_key,
            rec,
            collections_by_key.get(ads_key, []),
            tag_prefix=tag_prefix_cli if tag_prefix_cli is not None else tag_prefix,
            keep_only_library=library_tags_only or keep_only_myads_tags,
            add_tags=add_keyword,
        )
        pdf_link = f'[[pdfs/{stem}.pdf]]' if os.path.exists(pdf_path) else ''
        existing = None
        if os.path.exists(note_path):
            with open(note_path, encoding='utf-8') as fin:
                existing = fin.read()
        abstract = strip_bib_braces(rec.get('abstract', ''))
        action = write_paper_note(
            note_path, catalogue, abstract, existing, pdf_link=pdf_link
        )
        if action == 'created':
            created += 1
        else:
            updated += 1

    print(f'Notes created={created} updated={updated} pdfs_downloaded={pdfs}')

    project_dir = os.path.join(root, 'projects', project_name)
    os.makedirs(project_dir, exist_ok=True)
    if project_collection and project_collection in library_records:
        project_recs = library_records[project_collection]
    elif project_citekeys.strip():
        keys = [item.strip() for item in project_citekeys.split(',')]
        project_recs = filter_records(all_records, keys)
    else:
        project_recs = all_records
    write_bib(os.path.join(project_dir, 'refs.bib'), project_recs)
    print(f'Wrote {len(project_recs)} entries to projects/{project_name}/refs.bib')


if __name__ == '__main__':
    args = parse_args()
    main(
        cli_vault=args.vault,
        cli_libraries=args.libraries,
        fetch_pdfs_flag=args.fetch_pdfs,
        reclean_only=args.reclean,
        tag_prefix_cli=args.tag_prefix,
        library_tags_only=args.library_tags_only,
    )
