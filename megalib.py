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


def main():
    headers = ads_auth_headers()
    config = biblib_config(headers)
    all_libraries = list_libraries(headers)
    mega = next(
        (lib for lib in all_libraries
         if lib['name'].lower() == mega_lib_name.lower()),
        None,
    )
    sources = select_libraries(all_libraries, skip_names=[mega_lib_name])
    print(f"Merging {len(sources)} libraries")
    my_bibs = unique_bibcodes(sources, config)
    print(f"Found {len(my_bibs)} unique bibcodes")

    if mega is None:
        url = ADS_BIBLIB_URL + "/libraries"
        payload = {
            "name": mega_lib_name,
            "description": mega_lib_description,
            "bibcode": my_bibs,
        }
    else:
        url = ADS_BIBLIB_URL + "/documents/" + mega['id']
        payload = {
            "name": mega_lib_name,
            "action": "add",
            "bibcode": my_bibs,
        }

    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload)
    )
    print(response)


if __name__ == '__main__':
    main()
