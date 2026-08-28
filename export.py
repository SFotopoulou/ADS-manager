import argparse
from core import (
    add_library_argument,
    ads_auth_headers,
    biblib_config,
    dict_to_bib,
    dict_to_csv,
    export_bibcodes,
    list_libraries,
    resolve_library_name,
    select_libraries,
    unique_bibcodes,
)

######### Parameters #########
# leave empty to export all your libraries or use comma-separated names of your libraries
library_name = ''
export_format = 'bibtex'  # citation style from ADS
export_filename = 'library'
export_filetype = 'bib'  # bib (default), csv
# A csv export is meant to help you keep track of the reading list, e.g. importing in Notion or topcat.
# If exporting in csv, keep a selection of columns. Ignored in bib.
# Select any of the Bibtex columns, and add extras that will appear empty in the CSV file.
columns = ['citekey', 'title', 'year', 'abstract', 'read status', 'relevance','author','journal',
            'keywords', 'doi', 'eprint','adsurl',
            ]

bibtex_keyformat = "%1H%R"
sort_format = "first_author asc"
#
# Use short or long journal names instead of journal TeX abbreviations; \aj
fix_journal = True
######################################


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export ADS libraries to a local BibTeX or CSV file.',
        epilog=(
            'Output name, format, and columns are set at the top of this script. '
            'Auth: ADS_API_TOKEN or a local mysecrets file.'
        ),
    )
    add_library_argument(parser)
    return parser.parse_args()


def main(cli_libraries=None):
    filetype = export_filetype.lower()
    if filetype == 'bib':
        convert_dict = dict_to_bib
        csv_columns = ''
    elif filetype == 'csv':
        convert_dict = dict_to_csv
        csv_columns = columns
    else:
        raise SystemExit(
            f'Unknown file format: {export_filetype}. Chose from (bib, csv).'
        )
    filename = f'{export_filename}.{export_filetype}'
    selected = resolve_library_name(cli_libraries, library_name)

    headers = ads_auth_headers()
    config = biblib_config(headers)
    my_libraries = select_libraries(list_libraries(headers), selected)
    print(f"Exporting from {len(my_libraries)} libraries")

    my_bibs = unique_bibcodes(my_libraries, config)
    print(f"Found {len(my_bibs)} unique bibcodes")

    expbib = export_bibcodes(
        my_bibs,
        headers,
        export_format=export_format,
        keyformat=bibtex_keyformat,
        sort_format=sort_format,
        fix_journal=fix_journal,
    )
    with open(filename, 'w') as fout:
        convert_dict(expbib, fout, columns=csv_columns)
    print(f'Library saved in {filename}')


if __name__ == '__main__':
    args = parse_args()
    main(cli_libraries=args.libraries)
