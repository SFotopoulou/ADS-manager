# Export ADS libraries into an Obsidian vault: paper notes, collection .bib files,
# optional arXiv PDFs, and a project subset for Overleaf.
import argparse
import os
import shutil
import requests
from core import (
    add_library_argument,
    ads_auth_headers,
    biblib_config,
    get_library,
    list_libraries,
    resolve_library_name,
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
    arxiv_id_from_record,
    filter_records,
    reclean_papers_dir,
    get_ads_token,
    records_from_bib,
    merge_plain_and_tagged,
    tag_library_records,
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
# Same tagging as tag.py → YAML `tags`
add_keyword = True
keep_only_myads_tags = False
tag_prefix = ''
# Overleaf subset: write projects/<project_name>/refs.bib
project_name = 'example'
# Empty = all exported citekeys; or comma-separated citekeys; or an ADS library slug
project_citekeys = ''
project_collection = ''
# If ADS is unreachable, build from these BibTeX files (empty = auto-detect)
offline_library_bib = 'library.bib'
offline_tagged_bib = 'library_tagged.bib'
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

Use the view tabs on the table: **Reading list**, **Unread**, and **By collection**. You can edit `read_status` and `relevance` in the table. `tags` come from ADS libraries (same rule as `tag.py`) plus keyword tags.

## Collections

Paper notes use `collections` from your ADS library names. Filter in the base with `collections.contains("your-library-slug")`.

Generated BibTeX:

- `bib/library.bib` — union of exported libraries
- `bib/library_tagged.bib` — same union with ADS library names in keywords
- `bib/collections/<library>.bib` — one file per ADS library
- `projects/example/refs.bib` — Overleaf subset (defaults to the full export)

Refresh from the repo root:

```bash
source .venv/bin/activate
python vault.py --vault /path/to/this/vault
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
        description='Export ADS libraries into an Obsidian vault.',
        epilog=(
            'Vault path, tagging, and project BibTeX defaults are set at the top of this script. '
            'Auth: ADS_API_TOKEN or a local mysecrets file. '
            'With --offline, notes are rebuilt from library.bib and library_tagged.bib.'
        ),
    )
    parser.add_argument(
        '--vault',
        metavar='PATH',
        help='Vault directory (overrides ADS_VAULT and the vault_root default)',
    )
    add_library_argument(parser, extra_help='Default: all except skip_libraries.')
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
    parser.add_argument(
        '--offline',
        action='store_true',
        help='Skip ADS and rebuild notes from library.bib and library_tagged.bib',
    )
    return parser.parse_args()


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
    config = biblib_config(headers)
    all_libraries = list_libraries(headers)
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


def find_offline_bib_paths(vault_root):
    """library.bib and library_tagged.bib: explicit paths, vault bib/, then cwd."""
    lib_candidates = []
    tagged_candidates = []
    if offline_library_bib.strip():
        lib_candidates.append(os.path.abspath(os.path.expanduser(offline_library_bib)))
    if offline_tagged_bib.strip():
        tagged_candidates.append(os.path.abspath(os.path.expanduser(offline_tagged_bib)))
    lib_candidates.extend([
        os.path.join(vault_root, 'bib', 'library.bib'),
        os.path.abspath('library.bib'),
    ])
    tagged_candidates.extend([
        os.path.join(vault_root, 'bib', 'library_tagged.bib'),
        os.path.abspath('library_tagged.bib'),
    ])

    def first_existing(paths):
        for path in paths:
            if path and os.path.isfile(path):
                return os.path.abspath(path)
        return ''

    return first_existing(lib_candidates), first_existing(tagged_candidates)


def load_from_bib_files(library_path, tagged_path):
    plain = records_from_bib(library_path) if library_path else {}
    tagged = records_from_bib(tagged_path) if tagged_path else {}
    if not plain and not tagged:
        raise FileNotFoundError(
            'Need library.bib and/or library_tagged.bib for an offline vault build.'
        )
    print(
        f'Loaded {len(plain)} records from {library_path or "(no library.bib)"}, '
        f'{len(tagged)} from {tagged_path or "(no library_tagged.bib)"}'
    )
    if not tagged:
        print('No library_tagged.bib; YAML tags will come from journal keywords only.')
    elif not plain:
        print('No library.bib; collections cannot be split from journal keywords.')
    return merge_plain_and_tagged(plain, tagged)


def filter_by_selected_libraries(library_records, all_records, collections_by_key,
                                 selected_libraries):
    """Keep records that belong to --library names (offline). Empty = all."""
    if not selected_libraries:
        return library_records, all_records, collections_by_key
    wanted = {
        slug_library_name(part.strip()).lower()
        for part in selected_libraries.split(',')
        if part.strip()
    }
    if not library_records:
        print('--library ignored offline: no collections (need library_tagged.bib).')
        return library_records, all_records, collections_by_key
    library_records = {
        slug: recs
        for slug, recs in library_records.items()
        if slug.lower() in wanted
    }
    if not library_records:
        raise NameError(f'No libraries found named: {sorted(wanted)}')
    keep = set()
    for recs in library_records.values():
        keep.update(recs)
    all_records = {key: rec for key, rec in all_records.items() if key in keep}
    collections_by_key = {
        key: [c for c in coll if slug_library_name(c).lower() in wanted]
        for key, coll in collections_by_key.items()
        if key in keep
    }
    return library_records, all_records, collections_by_key


def write_catalogue_bibs(root, library_records, all_records, tag_prefix_value,
                         keep_only_library):
    for slug, recs in library_records.items():
        write_bib(os.path.join(root, 'bib', 'collections', slug + '.bib'), recs)
    write_bib(os.path.join(root, 'bib', 'library.bib'), all_records)
    tagged = tag_library_records(
        library_records,
        tag_prefix=tag_prefix_value,
        keep_only_library=keep_only_library,
        add_keyword=add_keyword,
    )
    write_bib(os.path.join(root, 'bib', 'library_tagged.bib'), tagged)


def copy_offline_bibs_into_vault(root, library_path, tagged_path):
    dest_lib = os.path.join(root, 'bib', 'library.bib')
    dest_tagged = os.path.join(root, 'bib', 'library_tagged.bib')
    os.makedirs(os.path.join(root, 'bib'), exist_ok=True)
    if library_path and os.path.abspath(library_path) != os.path.abspath(dest_lib):
        shutil.copy2(library_path, dest_lib)
        print(f'Copied {library_path} → {dest_lib}')
    if tagged_path and os.path.abspath(tagged_path) != os.path.abspath(dest_tagged):
        shutil.copy2(tagged_path, dest_tagged)
        print(f'Copied {tagged_path} → {dest_tagged}')


def load_from_ads_or_bib(root, selected, force_offline=False):
    """ADS first; on failure or --offline, library.bib + library_tagged.bib."""
    ads_error = None
    if not force_offline and token_available():
        try:
            return load_from_ads(selected), True
        except (FileNotFoundError, OSError, ValueError, KeyError,
                requests.RequestException) as exc:
            ads_error = exc
            print(f'ADS unavailable ({exc}); falling back to local BibTeX')
    elif not force_offline:
        ads_error = 'no ADS token'
        print('No ADS token; falling back to local BibTeX')
    else:
        print('Offline mode: using local BibTeX')

    library_path, tagged_path = find_offline_bib_paths(root)
    if not library_path and not tagged_path:
        hint = f' ({ads_error})' if ads_error else ''
        raise FileNotFoundError(
            'Set ADS_API_TOKEN or provide library.bib and library_tagged.bib '
            f'in the vault bib/ folder or the working directory.{hint}'
        )
    loaded = load_from_bib_files(library_path, tagged_path)
    loaded = filter_by_selected_libraries(*loaded, selected)
    copy_offline_bibs_into_vault(root, library_path, tagged_path)
    return loaded, False


def main(cli_vault=None, cli_libraries=None, fetch_pdfs_flag=False,
         reclean_only=False, tag_prefix_cli=None, library_tags_only=False,
         force_offline=False):
    root = resolve_vault_root(cli_vault)
    ensure_vault_layout(root)
    if reclean_only:
        n = reclean_papers_dir(os.path.join(root, 'papers'))
        print(f'Recleaned {n} paper notes in {root}')
        return
    selected = resolve_library_name(cli_libraries, library_name)
    prefix = tag_prefix_cli if tag_prefix_cli is not None else tag_prefix
    keep_only = library_tags_only or keep_only_myads_tags

    (library_records, all_records, collections_by_key), from_ads = load_from_ads_or_bib(
        root, selected, force_offline=force_offline
    )
    if from_ads:
        write_catalogue_bibs(root, library_records, all_records, prefix, keep_only)
    print(f'{len(all_records)} unique records into {root}')

    created = updated = pdfs = pdf_exists = pdf_no_arxiv = 0
    papers_dir = os.path.join(root, 'papers')
    pdfs_dir = os.path.join(root, 'pdfs')

    for ads_key, rec in all_records.items():
        citekey = citekey_from_ads_key(ads_key)
        stem = safe_note_stem(citekey)
        note_path = os.path.join(papers_dir, stem + '.md')
        pdf_path = os.path.join(pdfs_dir, stem + '.pdf')
        existing = None
        if os.path.exists(note_path):
            with open(note_path, encoding='utf-8') as fin:
                existing = fin.read()
        if fetch_pdfs_flag or fetch_pdfs:
            if os.path.exists(pdf_path):
                pdf_exists += 1
            else:
                arxiv_id = arxiv_id_from_record(rec, existing)
                if not arxiv_id:
                    pdf_no_arxiv += 1
                    print(f'PDF skip {citekey}: no arXiv id')
                else:
                    try:
                        if download_arxiv_pdf(arxiv_id, pdf_path):
                            pdfs += 1
                    except Exception as exc:
                        print(f'PDF skip {citekey}: {exc}')
        catalogue = record_catalogue(
            ads_key,
            rec,
            collections_by_key.get(ads_key, []),
            tag_prefix=prefix if from_ads else '',
            keep_only_library=keep_only,
            add_tags=add_keyword,
        )
        pdf_link = f'[[pdfs/{stem}.pdf]]' if os.path.exists(pdf_path) else ''
        abstract = strip_bib_braces(rec.get('abstract', ''))
        action = write_paper_note(
            note_path, catalogue, abstract, existing, pdf_link=pdf_link
        )
        if action == 'created':
            created += 1
        else:
            updated += 1

    print(f'Notes created={created} updated={updated}')
    if fetch_pdfs_flag or fetch_pdfs:
        print(
            f'PDFs downloaded={pdfs} already_present={pdf_exists} '
            f'no_arxiv={pdf_no_arxiv}'
        )

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
        force_offline=args.offline,
    )
