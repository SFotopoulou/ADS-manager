# Intented usage: use keywords to filter paper selection, e.g. in Zotero
# Each bibcode will be saved once in one large library.
# Add keyword with library name and optional prefix per paper to retain library categorisation in ADS
import math
import requests
import json
from ads_lib import ads_auth_headers, dict_to_bib, get_library
from ads_lib import fix_journal_abbr
from ads_lib import adsresponse_to_dict, sanitise_multi, add_keyword_tag

######### Parameters #########
export_filename = 'export_tagged.bib'
export_format = 'bibtexabs'
# leave empty to export all your libraries
# or use comma-separated names of your libraries
library_name = ''
bibtex_keyformat = "%1H%R"
sort_format = "first_author asc"
# Use short or long journal names instead of journal TeX abbreviations; \aj
fix_journal = True
add_keyword = True
keep_only_myads_tags = False
tag_prefix = ''
######################################

# Connect to ADS
base_url = "https://api.adsabs.harvard.edu/v1/biblib"
headers = ads_auth_headers()

# Find all your libraries
r = requests.get(base_url+"/libraries",
                 headers=headers)
all_libraries = r.json()['libraries']

if library_name == '':
    my_libraries = all_libraries
else:
    libs = library_name.split(',')
    lib_list = [l.lower().strip() for l in libs]
    my_libraries = []
    my_libraries = [
        lib for lib in all_libraries if lib['name'].lower() in lib_list]
    if len(my_libraries)==0:
        raise NameError(f"No libraries found named: {lib_list}")

print("Exporting from {} libraries".format(str(len(my_libraries))))

# Get bibcodes for each library
config = {}
config['headers'] = headers
config['url'] = base_url

bibcode_sum = 0
response = None

megalib = []
for library in my_libraries:
    # empty scapes and underscores are replaced by "-"
    lib_name = library['name'].replace(' ', '-').replace('_','-')
    #
    # get bibcodes
    my_bibs = get_library(library['id'], library['num_documents'], config)
    #
    bibcode_sum = bibcode_sum + len(my_bibs)
    print(f"{lib_name} has {len(my_bibs)} bibcodes")
    #
    export_url = "https://api.adsabs.harvard.edu/v1/export/"+export_format
    #
    start = 0
    rows = 2000
    num_paginates = int(math.ceil(len(my_bibs) / (1.0*rows)))
    #
    s1 = start
    s2 = rows
    #
    for i in range(num_paginates):
        #
        querystring = {"bibcode": my_bibs[s1:s2],
                       "keyformat": bibtex_keyformat,
                       "sort": sort_format}
        #
        response = requests.request("POST",
                                    export_url,
                                    headers=headers,
                                    data=json.dumps(querystring))
        #
        # turn response into dictionary of references
        expbib = adsresponse_to_dict(response.json()['export'])
        #
        if fix_journal == True:
            expbib = fix_journal_abbr(expbib, format='short')
        #
        if add_keyword == True:
            expbib = add_keyword_tag(expbib, 
                                    tag=f'{tag_prefix}{lib_name}',
                                    only_myads=keep_only_myads_tags)
        #   
        megalib.append( expbib )
        #
        s1 = s1 + rows
        s2 = s2 + rows
        
# sanitise multiple occurencies; merge keywords
if not megalib:
    raise SystemExit("No records to export.")

final_dict = sanitise_multi(megalib)
uniq_bibcodes = len(final_dict.keys())
if bibcode_sum == 0:
    print("Total 0 bibcodes")
else:
    print(f"Total {bibcode_sum} bibcodes, {uniq_bibcodes} unique ({round(100*uniq_bibcodes/bibcode_sum, 1)}%)")

with open(export_filename, 'w') as fout:
    dict_to_bib(final_dict, fout)

print(f"Output in {export_filename}")
if response is not None:
    print(response)
