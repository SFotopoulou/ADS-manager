# Literature

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
