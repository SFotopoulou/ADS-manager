import requests
import json
from ads_lib import ads_auth_headers, get_library


######### Parameters #########
mega_lib_name = 'MEGALIB'
mega_lib_description = "Union of all libraries"
######################################

base_url = "https://api.adsabs.harvard.edu/v1/biblib"
headers = ads_auth_headers()
######################################

# Get all your libraries
r = requests.get(base_url+"/libraries",
                 headers=headers)
my_libraries = r.json()['libraries']

# Get bibcodes for each library, skipping mega_lib_name if it already exists
bibs = []
config = {}

config['headers'] = headers
config['url'] = base_url

mega_lib_id = 0
source_count = 0

for library in my_libraries:

    if library['name'] == mega_lib_name:
        mega_lib_id = library['id']
        continue

    source_count += 1
    bib = get_library(library['id'], library['num_documents'], config)

    bibs.extend(bib)

print("Merging {} libraries".format(str(source_count)))

# Keep unique bibcodes
my_bibs = list(set(bibs))
print("Found {} unique bibcodes".format(len(my_bibs)))


if mega_lib_id == 0:
    # Create mega_lib_name if it does not exist.
    url = base_url+"/libraries"

    querystring = {"name": mega_lib_name,
                   "description": mega_lib_description,
                   "bibcode": my_bibs}

    response = requests.request("POST",
                                url,
                                headers=headers,
                                data=json.dumps(querystring))

    print(response)

else:
    # If mega_lib_name exists, add the union of other libraries.
    url = base_url+"/documents/"+mega_lib_id

    querystring = {"name": mega_lib_name,
                   "action": "add",
                   "bibcode": my_bibs}

    response = requests.request("POST",
                                url,
                                headers=headers,
                                data=json.dumps(querystring))

    print(response)
