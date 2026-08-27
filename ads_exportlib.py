import math
import requests
import json
from ads_lib import ads_auth_headers, get_library
from ads_lib import fix_journal_abbr
from ads_lib import adsresponse_to_dict, dict_to_bib, dict_to_csv

######### Parameters #########
# leave empty to export all your libraries or use comma-separated names of your libraries
library_name = ''
export_format = 'bibtex'  # citation style from ADS
export_filename = 'export_bib'
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
# Validate saved file type
if export_filetype.lower() == 'bib':
    convert_dict = dict_to_bib
    columns = ''
elif export_filetype.lower() == 'csv':
    convert_dict = dict_to_csv
else:
    exit(f'Unknown file format: {export_filetype}. Chose from (bib, csv).')
filename = f'{export_filename}.{export_filetype}'

#
# Connect to ADS account
base_url = "https://api.adsabs.harvard.edu/v1/biblib"
headers = ads_auth_headers()

# Finds all your libraries
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
bibs = []
config = {}
config['headers'] = headers
config['url'] = base_url

for library in my_libraries:
    #
    bib = get_library(library['id'], library['num_documents'], config)
    #
    bibs.extend(bib)

# Keep unique bibcodes
my_bibs = list(set(bibs))
print("Found {} unique bibcodes".format(len(my_bibs)))

export_url = "https://api.adsabs.harvard.edu/v1/export/"+export_format

start = 0
rows = 2000
num_paginates = int(math.ceil(len(my_bibs) / (1.0*rows)))

s1 = start
s2 = rows

expbib = {}
response = None

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
    # turn response into dictionary of references
    temp_bib = adsresponse_to_dict(response.json()['export'])

    if fix_journal == True:
        temp_bib = fix_journal_abbr(temp_bib, format='short')

    for key, value in temp_bib.items():
        expbib[key] = value

    s1 = s1 + rows
    s2 = s2 + rows


with open(filename, 'w') as fout:
    final_bib = convert_dict(expbib, fout, columns=columns)

if response is not None:
    print(response)
print(f'Library saved in {filename}')
