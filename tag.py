# Intented usage: use keywords to filter paper selection, e.g. in Zotero
# Each bibcode will be saved once in one large library.
# Add keyword with library name and optional prefix per paper to retain library categorisation in ADS
import argparse
from core import (
    add_keyword_tag,
    add_library_argument,
    ads_auth_headers,
    biblib_config,
    dict_to_bib,
    export_bibcodes,
    get_library,
    list_libraries,
    resolve_library_name,
    sanitise_multi,
    select_libraries,
    slug_library_name,
)

######### Parameters #########
export_filename = 'library_tagged.bib'
export_format = 'bibtexabs'
# leave empty to export all your individual libraries
# or use comma-separated names of your libraries
library_name = ''
# Union library is not a collection unless named with --library
skip_libraries = 'MEGALIB'
bibtex_keyformat = "%1H%R"
sort_format = "first_author asc"
# Use short or long journal names instead of journal TeX abbreviations; \aj
fix_journal = True
add_keyword = True
keep_only_myads_tags = False
tag_prefix = ''
######################################


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export ADS libraries to BibTeX with library names as keywords.',
        epilog=(
            'Output filename, keyword tagging, and tag_prefix are set at the top of this script. '
            'Auth: ADS_API_TOKEN or a local mysecrets file.'
        ),
    )
    add_library_argument(
        parser,
        extra_help='Default: all individual libraries (not MEGALIB).',
    )
    return parser.parse_args()


def main(cli_libraries=None):
    selected = resolve_library_name(cli_libraries, library_name)
    headers = ads_auth_headers()
    config = biblib_config(headers)
    skip_names = [n.strip() for n in skip_libraries.split(',') if n.strip()]
    my_libraries = select_libraries(
        list_libraries(headers), selected, skip_names=skip_names
    )
    print(f"Exporting from {len(my_libraries)} libraries")

    tagged = []
    bibcode_sum = 0
    for library in my_libraries:
        lib_name = slug_library_name(library['name'])
        my_bibs = get_library(library['id'], library['num_documents'], config)
        bibcode_sum += len(my_bibs)
        print(f"{lib_name} has {len(my_bibs)} bibcodes")
        if not my_bibs:
            continue
        expbib = export_bibcodes(
            my_bibs,
            headers,
            export_format=export_format,
            keyformat=bibtex_keyformat,
            sort_format=sort_format,
            fix_journal=fix_journal,
        )
        if add_keyword:
            expbib = add_keyword_tag(
                expbib,
                tag=f'{tag_prefix}{lib_name}',
                only_myads=keep_only_myads_tags,
            )
        tagged.append(expbib)

    if not tagged:
        raise SystemExit("No records to export.")

    final_dict = sanitise_multi(tagged)
    uniq = len(final_dict)
    if bibcode_sum == 0:
        print("Total 0 bibcodes")
    else:
        pct = round(100 * uniq / bibcode_sum, 1)
        print(f"Total {bibcode_sum} bibcodes, {uniq} unique ({pct}%)")

    with open(export_filename, 'w') as fout:
        dict_to_bib(final_dict, fout)
    print(f"Output in {export_filename}")


if __name__ == '__main__':
    args = parse_args()
    main(cli_libraries=args.libraries)
