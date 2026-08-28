# ADS library and markdown reference manager

Shared helpers live in `core.py` (auth, library fetch, export parsing, journal names, keyword tagging, and file output). The scripts below import from that module.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`tag.py` expands numeric ADS/UAT keyword codes using `UAT_list.json` (Unified Astronomy Thesaurus). A copy is included in this repo. To refresh it, download [UAT_list.json](https://github.com/astrothesaurus/UAT) from the official UAT repository and place it next to `core.py`.

## Usage

Provide your ADS API token in one of these ways (checked in order):

1. Environment variable (preferred; keeps the token out of the project folder):

```bash
export ADS_API_TOKEN='your-token-here'
```

To avoid storing the token in shell history, put it in a private file outside the repo (`chmod 600`) and source that file:

```bash
# ~/.config/ads_megalib/env
export ADS_API_TOKEN='your-token-here'
```

```bash
source ~/.config/ads_megalib/env
```

2. A local `mysecrets` file in the same folder as the scripts (see `example_mysecrets`). This file is gitignored and listed in `.cursorignore`.

The code will use your token and fetch your library information.

## Scripts
### Union of all libraries on ADS
`megalib.py` **creates or updates a library on your ADS account** that is the union of all of your other libraries. Useful for using the metrics tools on ADS. Re-runs skip the mega library itself so its bibcodes are not fed back into the union.

`python megalib.py`

### Export locally, preserve ADS library as keyword
`tag.py` exports all or some of your libraries into a single local `.bib` file and edits the keywords to include the name of the ADS library.

`python tag.py --library JADES`

Repeat `--library` or comma-separate names. Omit it to export all libraries (or those in `library_name` at the top of the script).

If the paper appears in more than one library, multiple keywords are used. Handy for filtering, e.g. with Zotero. Optionally: use the names of the libraries as the only keywords, useful to avoid a very long list of keywords from the journals. When keeping existing keywords, numeric UAT codes are expanded to human-readable names via `UAT_list.json`.

If `fix_journal` is True (default) and an entry that should have a BibTeX `journal` field is missing it, a warning is raised.
Suppress all warnings with:

`python -Wignore tag.py`

### Export libraries locally - plain version
`export.py` exports all or some of your libraries into a single local file (`.bib` or `.csv`). No optimisation on keywords.

`python export.py --library JADES`

Same `--library` rule as `tag.py`.

If `fix_journal` is True (default) and an entry that should have a BibTeX `journal` field is missing it, a warning is raised.
Suppress all warnings with:

`python -Wignore export.py`

### Export into an Obsidian vault
`vault.py` writes ADS libraries into a vault (default `example_vault/`): one markdown note per citekey (with YAML `tags`), per-collection BibTeX, `bib/library.bib`, `bib/library_tagged.bib`, and `projects/<name>/refs.bib` for Overleaf.

Re-runs refresh catalogue YAML from ADS and do **not** overwrite `read_status`, `relevance`, `pdf`, or the note body below `<!-- ads-body -->`.

`python vault.py --vault /path/to/your/vault --library "ML - unsupervised learning" --fetch-pdfs`

`--vault` wins over `ADS_VAULT`, which wins over the `vault_root` default (`example_vault/`). `~` is expanded.

Repeat `--library` or comma-separate names. Omit it to export all libraries except those in `skip_libraries`.

`--fetch-pdfs` downloads arXiv PDFs into `pdfs/{citekey}.pdf` when an `eprint` is present and the file is not already there. Publisher PDFs are not fetched (paywall); drop those into `pdfs/` yourself.

If ADS is unreachable (no token, network, or API error), `vault.py` rebuilds notes from `library.bib` plus `library_tagged.bib`. It looks in the vault `bib/` folder, then the working directory (the files written by `export.py` and `tag.py`). Force that path with `--offline`.

Open the vault folder in Obsidian 1.9+. Enable the **Bases** core plugin (tables) and **PDF++** (annotation). ADS remains the catalogue; this vault is the reading and writing layer.

## Megalib parameters

At the top of `megalib.py` you can adjust the name and description of the new ADS library.

`mega_lib_name = 'MEGALIB'`

`mega_lib_description = "Union of all libraries"`

This script writes to your ADS account. If a library named `mega_lib_name` already exists, bibcodes from your other libraries are added to it.

## Exportlib parameters

At the top of `export.py` you can choose:

which libraries to export. Prefer `--library "My ADS library"`. Repeat or comma-separate. Empty = all:

`library_name = ''`

the [output format](http://adsabs.github.io/help/actions/export):

`export_format = 'bibtex'`

the output filename without extension (overwritten if exists; the extension comes from `export_filetype`):

`export_filename = 'library'`

the saved file type, `bib` or `csv`:

`export_filetype = 'bib'`

A CSV export is meant to help you keep track of a reading list, e.g. importing in Notion or TOPCAT. For CSV, choose columns (ignored for bib). BibTeX fields are filled when present; extra columns such as `read status` and `relevance` are written empty/`false`:

`columns = ['citekey', 'title', 'year', 'abstract', 'read status', 'relevance', 'author', 'journal', 'keywords', 'doi', 'eprint', 'adsurl']`

the [keyword format](http://adsabs.github.io/help/actions/export):

`bibtex_keyformat = "%1H%R"`

the [sorting of your references:](http://adsabs.github.io/help/actions/sort)

`sort_format = "first_author asc"`

expand TeX journal abbreviations such as `\aj` to short names (e.g. AJ). Set to False to leave them unchanged:

`fix_journal = True`

## Tag export parameters

At the top of `tag.py` you can choose:

the exported filename (overwritten if exists; `.bib` only):

`export_filename = 'library_tagged.bib'`

the [output format](http://adsabs.github.io/help/actions/export):

`export_format = 'bibtexabs'`

which libraries to export. Prefer `--library "My ADS library"`. Repeat or comma-separate. Empty = all:

`library_name = ''`

the [keyword format](http://adsabs.github.io/help/actions/export):

`bibtex_keyformat = "%1H%R"`

the [sorting of your references:](http://adsabs.github.io/help/actions/sort)

`sort_format = "first_author asc"`

expand TeX journal abbreviations to short names:

`fix_journal = True`

add the ADS library name as a keyword:

`add_keyword = True`

replace existing keywords with library names only (the “library tags only” option). Leave False to keep journal keywords and expand UAT codes:

`keep_only_myads_tags = False`

optional prefix prepended to each library tag:

`tag_prefix = ''`

## Vault parameters

At the top of `vault.py`:

vault folder. Prefer `python vault.py --vault /path/to/vault`. Else `ADS_VAULT`, else:

`vault_root = 'example_vault'`

which libraries to export. Prefer `--library "My ADS library"`. Repeat or comma-separate. Empty = all, except `skip_libraries`:

`library_name = ''`

`skip_libraries = 'MEGALIB'`

the [output format](http://adsabs.github.io/help/actions/export) (include abstracts for notes):

`export_format = 'bibtexabs'`

download missing arXiv PDFs into `pdfs/{citekey}.pdf` (never overwrites). Prefer `--fetch-pdfs`, or:

`fetch_pdfs = False`

ADS library names as Obsidian `tags` (same slug rule as `tag.py`). Also add keyword tags unless `keep_only_myads_tags` is True:

`add_keyword = True`

`keep_only_myads_tags = False`

`tag_prefix = ''`

Or: `python vault.py --tag-prefix my- --library-tags-only`

Overleaf subset directory and optional citekey/collection filter:

`project_name = 'example'`

`project_citekeys = ''`

`project_collection = ''`

If ADS is unavailable, rebuild from `export.py` / `tag.py` output (`library.bib` and `library_tagged.bib`). Empty = auto-detect in vault `bib/` then the working directory:

`offline_library_bib = ''`

`offline_tagged_bib = ''`

Or: `python vault.py --vault /path/to/vault --offline`

