import argparse
import json
import requests
from core import (
    ADS_BIBLIB_URL,
    ads_auth_headers,
    biblib_config,
    list_libraries,
    select_libraries,
    unique_bibcodes,
)


######### Parameters #########
mega_lib_name = 'MEGALIB'
mega_lib_description = "Union of all libraries"
######################################


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            'Create or update an ADS library that is the union of all your '
            'other libraries. Re-runs skip the mega library so its bibcodes '
            'are not merged into itself.'
        ),
        epilog=(
            'Auth: ADS_API_TOKEN or a local mysecrets file. '
            'Description defaults to mega_lib_description at the top of this script.'
        ),
    )
    parser.add_argument(
        '--name',
        metavar='NAME',
        default=None,
        help=f'Name of the merged ADS library (default: {mega_lib_name!r})',
    )
    return parser.parse_args()


def main(cli_name=None):
    name = (cli_name or mega_lib_name).strip() or mega_lib_name
    headers = ads_auth_headers()
    config = biblib_config(headers)
    all_libraries = list_libraries(headers)
    mega = next(
        (lib for lib in all_libraries
         if lib['name'].lower() == name.lower()),
        None,
    )
    sources = select_libraries(all_libraries, skip_names=[name])
    print(f"Merging {len(sources)} libraries into {name!r}")
    my_bibs = unique_bibcodes(sources, config)
    print(f"Found {len(my_bibs)} unique bibcodes")

    if mega is None:
        url = ADS_BIBLIB_URL + "/libraries"
        payload = {
            "name": name,
            "description": mega_lib_description,
            "bibcode": my_bibs,
        }
    else:
        url = ADS_BIBLIB_URL + "/documents/" + mega['id']
        payload = {
            "name": name,
            "action": "add",
            "bibcode": my_bibs,
        }

    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload)
    )
    print(response)


if __name__ == '__main__':
    args = parse_args()
    main(cli_name=args.name)
