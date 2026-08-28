# ADS library and markdown reference manager

This is package to help manage [ADS/Scixplorer](https://scixplorer.org/) libraries (download, merge, add keywords) and create a reference manager using [Obsidian](https://obsidian.md/). The script 'vault.py' create a local vault in a specified location, downloads the selected libraries, and optionally the PDF from [arXiv](https://arxiv.org/).

## Quick Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ADS authentication

Provide your [ADS API token](https://ui.adsabs.harvard.edu/help/api/) in one of these ways (checked in order):

1. Environment variable (preferred; keeps the token out of the project folder):

```bash
export ADS_API_TOKEN='your-token-here'
```

To avoid storing the token in shell history, put it in a private file outside the repo (`chmod 600`) and source that file:

```bash
# ~/.config/ADS-manager/env
export ADS_API_TOKEN='your-token-here'
```

```bash
source ~/.config/ADS-manager/env
```

2. A local `mysecrets` file in the same folder as the scripts (see `example_mysecrets`), this file is gitignored.

The code will use your token and fetch your library information.

## Scripts

See also [Script Parameters](https://github.com/SFotopoulou/ADS-manager/tree/master#script-parameters) for a detailed options list.

### Export libraries locally - plain version
```
python export.py --help
usage: export.py [-h] [--library NAME]

Export ADS libraries to a local BibTeX or CSV file.

options:
  -h, --help      show this help message and exit
  --library NAME  ADS library to export. Repeat for several, or comma-separate. Default: all.
```

Output name, format, and columns are set at the top of this script. Auth: ADS_API_TOKEN or a local
mysecrets file.

`export.py` exports all or some of your libraries into a single local file (`.bib` or `.csv`). No optimisation on keywords.

Repeat `--library` or comma-separate names. Omit it to export all libraries (or those in `library_name` at the top of the script).

If `fix_journal` is True (default) and an entry that should have a BibTeX `journal` field is missing it, a warning is raised.
Suppress all warnings with:

`python -Wignore export.py`


### Export locally, preserve ADS library as keyword
```
python tag.py --help
usage: tag.py [-h] [--library NAME]

Export ADS libraries to BibTeX with library names as keywords.

options:
  -h, --help      show this help message and exit
  --library NAME  ADS library to export. Repeat for several, or comma-separate. Default: all.

Output filename, keyword tagging, and tag_prefix are set at the top of this script. Auth: ADS_API_TOKEN
or a local mysecrets file.
```

`tag.py` exports all or some of your libraries into a single local `.bib` file and edits the keywords to include the name of the ADS library.

Repeat `--library` or comma-separate names. Omit it to export all libraries (or those in `library_name` at the top of the script).

If the paper appears in more than one library, multiple keywords are used. Handy for filtering, e.g. with Zotero. Optionally: use the names of the libraries as the only keywords, useful to avoid a very long list of keywords from the journals. When keeping existing keywords, numeric UAT codes are expanded to human-readable names via `UAT_list.json`.

If `fix_journal` is True (default) and an entry that should have a BibTeX `journal` field is missing it, a warning is raised.
Suppress all warnings with:

`python -Wignore tag.py`

### Union of all libraries on ADS
```
python megalib.py --help                 ok | ads_megalib py | at 10:16:11 
usage: megalib.py [-h] [--name NAME]

Create or update an ADS library that is the union of all your other libraries. Re-runs skip the mega
library so its bibcodes are not merged into itself.

options:
  -h, --help   show this help message and exit
  --name NAME  Name of the merged ADS library (default: 'MEGALIB')

Auth: ADS_API_TOKEN or a local mysecrets file. Description defaults to mega_lib_description at the top of
this script.
```
`megalib.py` **creates or updates a library on your ADS account** that is the union of all of your other libraries. Useful for using the metrics tools on ADS. Re-runs skip the mega library itself so its bibcodes are not fed back into the union.



### Export into an Obsidian vault
```
python vault.py --help                   ok | ads_megalib py | at 10:16:04 
usage: vault.py [-h] [--vault PATH] [--library NAME] [--fetch-pdfs] [--reclean] [--tag-prefix PREFIX]
                [--library-tags-only] [--offline]

Export ADS libraries into an Obsidian vault.

options:
  -h, --help           show this help message and exit
  --vault PATH         Vault directory (overrides ADS_VAULT and the vault_root default)
  --library NAME       ADS library to export. Repeat for several, or comma-separate. Default: all except
                       skip_libraries.
  --fetch-pdfs         Download missing arXiv PDFs into pdfs/{citekey}.pdf (never overwrites)
  --reclean            Rewrite existing paper notes with cleaned titles/authors/abstracts; skip ADS fetch
  --tag-prefix PREFIX  Prefix for ADS library tags (overrides tag_prefix in the script)
  --library-tags-only  YAML tags are only ADS library names (same as keep_only_myads_tags)
  --offline            Skip ADS and rebuild notes from library.bib and library_tagged.bib

Vault path, tagging, and project BibTeX defaults are set at the top of this script. Auth: ADS_API_TOKEN
or a local mysecrets file. With --offline, notes are rebuilt from library.bib and library_tagged.bib.
```

`vault.py` writes ADS libraries into a vault (default `example_vault/`): one markdown note per citekey (with YAML `tags`), per-collection BibTeX, `bib/library.bib`, `bib/library_tagged.bib`, and `projects/<name>/refs.bib` for Overleaf.

Re-runs refresh catalogue YAML from ADS and do **not** overwrite `read_status`, `relevance`, `pdf`, or the note body below `<!-- ads-body -->`.

`--vault` wins over `ADS_VAULT`, which wins over the `vault_root` default (`example_vault/`). `~` is expanded.

Repeat `--library` or comma-separate names. Omit it to export all libraries except those in `skip_libraries`.

`--fetch-pdfs` downloads arXiv PDFs into `pdfs/{citekey}.pdf` when an `eprint` is present and the file is not already there. Publisher PDFs are not fetched (paywall); drop those into `pdfs/` yourself.

If ADS is unreachable (no token, network, or API error), `vault.py` rebuilds notes from `library.bib` plus `library_tagged.bib`. It looks in the vault `bib/` folder, then the working directory (the files written by `export.py` and `tag.py`). Force that path with `--offline`.

Open the vault folder in Obsidian 1.9+. Enable the **Bases** core plugin (tables) and **PDF++** (annotation). ADS remains the catalogue; this vault is the reading and writing layer.

## Script parameters

### Exportlib parameters

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

### Tag export parameters

`tag.py` expands numeric ADS/UAT keyword codes using `UAT_list.json` (Unified Astronomy Thesaurus). A copy is included in this repo. To refresh it, download [UAT_list.json](https://github.com/astrothesaurus/UAT) from the official UAT repository and place it next to `core.py`.
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

### Megalib parameters
At the top of `megalib.py` you can adjust the name and description of the new ADS library.

`mega_lib_name = 'MEGALIB'`

`mega_lib_description = "Union of all libraries"`

This script writes to your ADS account. If a library named `mega_lib_name` already exists, bibcodes from your other libraries are added to it.

### Vault parameters

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

