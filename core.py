import math
import os
import copy
import requests
import json
import warnings
from collections import OrderedDict

# Unified Astronomy Thesaurus (UAT)
# https://astrothesaurus.org/
# https://github.com/astrothesaurus/UAT
UAT_LIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'UAT_list.json')
ADS_BIBLIB_URL = 'https://api.adsabs.harvard.edu/v1/biblib'
uris = None


def _load_uat(path=UAT_LIST_PATH):
    """Load UAT_list.json into a uri-number -> name mapping."""
    global uris
    if uris is not None:
        return uris
    try:
        with open(path) as f:
            thesaurus = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "UAT_list.json is required to expand numeric ADS keywords. "
            "Download it from https://github.com/astrothesaurus/UAT "
            "(UAT_list.json) and place it next to core.py."
        ) from exc
    mapping = {}
    for item in thesaurus:
        name = item['name']
        number = int(item['uri'].split('/')[-1])
        mapping[number] = name
    uris = mapping
    return uris


def get_ads_token(secrets_path='mysecrets'):
    """Return the ADS API token from ADS_API_TOKEN, else a local secrets file."""
    token = os.environ.get('ADS_API_TOKEN', '').strip()
    if token:
        return token
    try:
        with open(secrets_path) as f:
            return json.load(f)['my_token']
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Set ADS_API_TOKEN or create a mysecrets file "
            "(see example_mysecrets)."
        ) from exc


def ads_auth_headers(token=None):
    """Return Authorization headers for the ADS API."""
    if token is None:
        token = get_ads_token()
    return {
        'Authorization': "Bearer " + token,
        "Content-type": "application/json",
    }


def journal_names():
    # from http://astro.dur.ac.uk/~cole/Intro_LaTeX_PG/PhDthesis/rcrain/aas_macros.sty

    short_name = {}
    long_name = {}

    short_name['\\aj'] = 'AJ'
    short_name['\\araa'] = r'ARA\&A'
    short_name['\\apj'] = 'ApJ'
    short_name['\\apjl'] = 'ApJ'
    short_name['\\apjs'] = 'ApJS'
    short_name['\\ao'] = 'Appl.~Opt.'
    short_name['\\apss'] = r'Ap\&SS'
    short_name['\\aap'] = r'A\&A'
    short_name['\\aapr'] = r'A\&A~Rev.'
    short_name['\\aaps'] = r'A\&AS'
    short_name['\\azh'] = 'AZh'
    short_name['\\baas'] = 'BAAS'
    short_name['\\jrasc'] = 'JRASC'
    short_name['\\memras'] = 'MmRAS'
    short_name['\\mnras'] = 'MNRAS'
    short_name['\\pra'] = 'Phys.~Rev.~A'
    short_name['\\prb'] = 'Phys.~Rev.~B'
    short_name['\\prc'] = 'Phys.~Rev.~C'
    short_name['\\prd'] = 'Phys.~Rev.~D'
    short_name['\\pre'] = 'Phys.~Rev.~E'
    short_name['\\prl'] = 'Phys.~Rev.~Lett.'
    short_name['\\pasp'] = 'PASP'
    short_name['\\pasj'] = 'PASJ'
    short_name['\\qjras'] = 'QJRAS'
    short_name['\\skytel'] = r'S\&T'
    short_name['\\solphys'] = 'Sol.~Phys.'
    short_name['\\sovast'] = 'Soviet~Ast.'
    short_name['\\ssr'] = 'Space~Sci.~Rev.'
    short_name['\\zap'] = 'ZAp'
    short_name['\\nat'] = 'Nature'
    short_name['\\iaucirc'] = 'IAU~Circ.'
    short_name['\\aplett'] = 'Astrophys.~Lett.'
    short_name['\\apspr'] = 'Astrophys.~Space~Phys.~Res.'
    short_name['\\bain'] = 'Bull.~Astron.~Inst.~Netherlands'
    short_name['\\fcp'] = 'Fund.~Cosmic~Phys.'
    short_name['\\gca'] = 'Geochim.~Cosmochim.~Acta'
    short_name['\\grl'] = 'Geophys.~Res.~Lett.'
    short_name['\\jcp'] = 'J.~Chem.~Phys.'
    short_name['\\jgr'] = 'J.~Geophys.~Res.'
    short_name['\\jqsrt'] = 'J.~Quant.~Spec.~Radiat.~Transf.'
    short_name['\\memsai'] = 'Mem.~Soc.~Astron.~Italiana'
    short_name['\\nphysa'] = 'Nucl.~Phys.~A'
    short_name['\\physrep'] = 'Phys.~Rep.'
    short_name['\\physscr'] = 'Phys.~Scr'
    short_name['\\planss'] = 'Planet.~Space~Sci.'
    short_name['\\procspie'] = 'Proc.~SPIE'
    # additional
    short_name['\\nar'] = 'New~Astr.~Rev.'
    short_name['\\na'] = 'New~Astr.'
    short_name['\\rmxaa'] = 'Rev.~Mexicana~de~Astron.~y~Astrof.'
    short_name['\\icarus'] = 'Icarus'
    short_name['\\pasa'] = 'PASA'
    short_name['\\jcap'] = 'JCAP'
    short_name['\\caa'] = r'ChA\&A'
    short_name['\\jaavso'] = 'JAVSO'
    short_name['\\psj'] = 'PSJ'
    short_name['\\actaa'] = 'AcA'    
    short_name['\\maps'] = r'M\&PS'

    long_name['\\aj'] = 'Astronomical Journal'
    long_name['\\araa'] = 'Annual Review of Astron and Astrophysics'
    long_name['\\apj'] = 'Astrophysical Journal'
    long_name['\\apjl'] = 'Astrophysical Journal, Letters'
    long_name['\\apjs'] = 'Astrophysical Journal, Supplement'
    long_name['\\ao'] = 'Applied Optics'
    long_name['\\apss'] = 'Astrophysics and Space Science'
    long_name['\\aap'] = 'Astronomy and Astrophysics'
    long_name['\\aapr'] = 'Astronomy and Astrophysics Reviews'
    long_name['\\aaps'] = 'Astronomy and Astrophysics, Supplement'
    long_name['\\azh'] = 'Astronomicheskii Zhurnal'
    long_name['\\baas'] = 'Bulletin of the AAS'
    long_name['\\jrasc'] = 'Journal of the RAS of Canada'
    long_name['\\memras'] = 'Memoirs of the RAS'
    long_name['\\mnras'] = 'Monthly Notices of the RAS'
    long_name['\\pra'] = 'Physical Review A: General Physics'
    long_name['\\prb'] = 'Physical Review B: Solid State'
    long_name['\\prc'] = 'Physical Review C'
    long_name['\\prd'] = 'Physical Review D'
    long_name['\\pre'] = 'Physical Review E'
    long_name['\\prl'] = 'Physical Review Letters'
    long_name['\\pasp'] = 'Publications of the ASP'
    long_name['\\pasj'] = 'Publications of the ASJ'
    long_name['\\qjras'] = 'Quarterly Journal of the RAS'
    long_name['\\skytel'] = 'ky and Telescope'
    long_name['\\solphys'] = 'Solar Physics'
    long_name['\\sovast'] = 'Soviet Astronomy'
    long_name['\\ssr'] = 'Space Science Reviews'
    long_name['\\zap'] = 'Zeitschrift fuer Astrophysik'
    long_name['\\nat'] = 'Nature'
    long_name['\\iaucirc'] = 'IAU Cirulars'
    long_name['\\aplett'] = 'Astrophysics Letters'
    long_name['\\apspr'] = 'Astrophysics Space Physics Research'
    long_name['\\bain'] = 'Bulletin Astronomical Institute of the Netherlands'
    long_name['\\fcp'] = 'Fundamental Cosmic Physics'
    long_name['\\gca'] = 'Geochimica Cosmochimica Acta'
    long_name['\\grl'] = 'Geophysics Research Letters'
    long_name['\\jcp'] = 'Journal of Chemical Physics'
    long_name['\\jgr'] = 'Journal of Geophysics Research'
    long_name['\\jqsrt'] = 'Journal of Quantitiative Spectroscopy and Radiative Transfer'
    long_name['\\memsai'] = 'Mem. Societa Astronomica Italiana'
    long_name['\\nphysa'] = 'Nuclear Physics A'
    long_name['\\physrep'] = 'Physics Reports'
    long_name['\\physscr'] = 'Physica Scripta'
    long_name['\\planss'] = 'Planetary Space Science'
    long_name['\\procspie'] = 'Proceedings of the SPIE'
    #
    long_name['\\nar'] = 'New Astronomy Review'
    long_name['\\na'] = 'New Astronomy'
    long_name['\\rmxaa'] = 'Revista Mexicana de Astronomia y Astrofisica'
    long_name['\\icarus'] = 'Icarus'
    long_name['\\pasa'] = 'Publications of the Astronomical Society of Australia'
    long_name['\\jcap'] = 'Journal of Cosmology and Astroparticle Physics'
    long_name['\\caa'] = 'Chinese Astronomy and Astrophysics'
    long_name['\\jaavso'] = 'Journal of the American Association of Variable Star Observers'
    long_name['\\psj'] = 'The Planetary Science Journal'
    long_name['\\actaa'] = 'Acta Astronomica'
    long_name['\\maps'] = 'Meteoritics and Planetary Science'
    return short_name, long_name

# Copied from ADS code, used to parse fieds

def __get_doc_type(self, solr_type):
    """
    convert from solr to BibTex document type

    :param solr_type:
    :return:
    """
    fields = {'article':'@ARTICLE', 'circular':'@ARTICLE', 'newsletter':'@ARTICLE',
                'bookreview':'@ARTICLE', 'erratum':'@ARTICLE', 'obituary':'@ARTICLE',
                'eprint':'@ARTICLE', 'catalog':'@ARTICLE', 'editorial':'@ARTICLE',
                'book':'@BOOK', 
                'inbook':'@INCOLLECTION',
                'proceedings':'@PROCEEDINGS', 
                'inproceedings':'@INPROCEEDINGS', 'abstract':'@INPROCEEDINGS',
                'misc':'@MISC', 'software':'@MISC','proposal':'@MISC', 'pressrelease':'@MISC',
                'talk':'@MISC',
                'phdthesis':'@PHDTHESIS','mastersthesis':'@MASTERSTHESIS',
                'techreport':'@MISC', 'intechreport':'@MISC'}
    return fields.get(solr_type, '')

def __get_fields(doc_type_bibtex):
    """
    exported fields for various document types

    :param a_doc:
    :return:
    """
    if (doc_type_bibtex == '@ARTICLE'):
        fields = [('author', 'author'), ('title', 'title'), ('pub', 'journal'),
                    ('keyword', 'keywords'), ('year', 'year'), ('month', 'month'),
                    ('volume', 'volume'), ('issue', 'number'), ('eid', 'eid'),
                    ('page_range', 'pages'), ('abstract', 'abstract'), ('doi', 'doi'),
                    ('eprintid', 'archivePrefix'), ('eprintid2', 'eprint'), ('arxiv_class', 'primaryClass'),
                    ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@BOOK'):
        fields = [('author', 'author'), ('title', 'title'),
                    ('year', 'year'), ('volume', 'volume'), ('doi', 'doi'),
                    ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@INCOLLECTION'):
        fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                    ('pub', 'booktitle'), ('year', 'year'), ('editor', 'editor'),
                    ('volume', 'volume'), ('series', 'series'), ('eid', 'eid'),
                    ('page_range', 'pages'), ('abstract', 'abstract'), ('doi', 'doi'),
                    ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@PROCEEDINGS'):
        fields = [('title', 'title'), ('keyword', 'keywords'), ('pub', 'booktitle'),
                    ('year', 'year'), ('editor', 'editor'), ('series', 'series'),
                    ('volume', 'volume'), ('month', 'month'), ('doi', 'doi'),
                    ('eprintid', 'archivePrefix'), ('eprintid2', 'eprint'), ('arxiv_class', 'primaryClass'),
                    ('abstract', 'abstract'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@INPROCEEDINGS'):
        fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                    ('pub', 'booktitle'), ('year', 'year'), ('editor', 'editor'),
                    ('series', 'series'), ('volume', 'volume'), ('month', 'month'),
                    ('eid', 'eid'), ('page_range', 'pages'), ('abstract', 'abstract'),
                    ('doi', 'doi'), ('eprintid', 'archivePrefix'), ('eprintid2', 'eprint'), ('arxiv_class', 'primaryClass'),
                    ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@MISC'):
        fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                    ('pub_raw', 'howpublished'), ('year', 'year'), ('month', 'month'),
                    ('eid', 'eid'), ('page_range', 'pages'), ('doi', 'doi'),
                    ('eprintid', 'archivePrefix'), ('eprintid2', 'eprint'), ('arxiv_class', 'primaryClass'),
                    ('version', 'version'), ('publisher', 'publisher'),
                    ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    elif (doc_type_bibtex == '@PHDTHESIS') or (doc_type_bibtex == '@MASTERSTHESIS'):
        fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                    ('aff', 'school'), ('year', 'year'), ('month', 'month'),
                    ('bibcode', 'adsurl'),('adsnotes', 'adsnote')]
    # 2/14 mapping techreport and intechreport to @MISC per Markus request for now
    # elif (doc_type_bibtex == '@TECHREPORT'):
    #     fields = [('author', 'author'), ('title', 'title'), ('pub_raw', 'journal'),
    #               ('keyword', 'keywords'), ('pub', 'booktitle'), ('year', 'year'),
    #               ('editor', 'editor'), ('series', 'series'), ('month', 'month'),
    #               ('eid', 'eid'), ('page_range', 'pages'), ('volume', 'volume'),
    #               ('doi', 'doi'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
    else:
        fields = []
    return OrderedDict(fields)

def get_library(library_id, num_documents, config):
    # from https://github.com/adsabs/ads-examples/blob/master/library_csv/lib_2_csv.py
    """
    Get the content of a library when you know its id. As we paginate the
    requests from the private library end point for document retrieval,
    we have to repeat requests until we have all documents.
    :param library_id: identifier of the library
    :type library_id:
    :param num_documents: number of documents in the library
    :type num_documents: int
    :return: list
    """

    start = 0
    rows = 2000  # max number of list length from API
    num_paginates = int(math.ceil(num_documents / (1.0*rows)))
    documents = []
    for i in range(num_paginates):
        #print('Pagination {} out of {}'.format(i+1, num_paginates))

        r = requests.get(
            '{}/libraries/{id}?start={start}&rows={rows}'.format(
                config['url'],
                id=library_id,
                start=start,
                rows=rows
            ),
            headers=config['headers']
        )

        # Get all the documents that are inside the library
        try:
            data = r.json()['documents']
        except ValueError:
            raise ValueError(r.text)

        documents.extend(data)

        start += rows

    return documents


def biblib_config(headers):
    """Config dict expected by get_library()."""
    return {'headers': headers, 'url': ADS_BIBLIB_URL}


def list_libraries(headers):
    """Return library metadata dicts from the ADS biblib API."""
    response = requests.get(
        ADS_BIBLIB_URL + '/libraries', headers=headers, timeout=30
    )
    payload = response.json()
    if 'libraries' not in payload:
        raise ValueError(payload)
    return payload['libraries']


def unique_bibcodes(libraries, config):
    """Union of bibcodes across libraries, first-seen order."""
    bibs = []
    for library in libraries:
        bibs.extend(get_library(library['id'], library['num_documents'], config))
    return list(dict.fromkeys(bibs))


def slug_library_name(name):
    """Filesystem- and YAML-friendly ADS library name."""
    return (name or '').replace(' ', '-').replace('_', '-')


def split_library_names(library_name):
    """Split a --library value into names; strips quotes around each part."""
    names = []
    for part in (library_name or '').split(','):
        part = part.strip().strip('\'"').strip()
        if part:
            names.append(part)
    return names


def normalize_library_query(name):
    """Lowercased slug for matching --library arguments to ADS names."""
    return slug_library_name(name.strip().strip('\'"').strip()).lower()


def wanted_library_slugs(library_name):
    return {normalize_library_query(part) for part in split_library_names(library_name)}


def slug_is_wanted(slug, wanted):
    if not wanted:
        return True
    return normalize_library_query(slug) in wanted


def collection_bib_stem(slug):
    """Filename stem for bib/collections/<stem>.bib."""
    text = slug_library_name(slug)
    text = ''.join(ch if ch.isalnum() or ch in '._-' else '-' for ch in text)
    return text.strip('-._') or 'collection'


def union_library_slugs(skip_names=None):
    """Lowercased names/slugs for union libraries (e.g. MEGALIB) that are not collections."""
    slugs = set()
    for name in skip_names or []:
        name = (name or '').strip()
        if not name:
            continue
        slugs.add(name.lower())
        slugs.add(slug_library_name(name).lower())
    return slugs


def is_union_library_name(name, skip_names=None):
    if not name:
        return False
    skip = union_library_slugs(skip_names)
    return name.lower() in skip or slug_library_name(name).lower() in skip


def select_libraries(all_libraries, library_name='', skip_names=None):
    """Filter ADS library metadata by comma-separated names; optionally skip some.

    Empty library_name means every library except skip_names (the union
    library, e.g. MEGALIB, is not treated as a collection). Explicit
    --library names are kept even if they appear in skip_names.
    """
    if library_name == '':
        return [
            lib for lib in all_libraries
            if not is_union_library_name(lib['name'], skip_names)
        ]
    lib_list = split_library_names(library_name)
    wanted_slugs = wanted_library_slugs(library_name)
    wanted = {name.lower() for name in lib_list} | {
        slug_library_name(name).lower() for name in lib_list
    } | wanted_slugs
    selected = [
        lib for lib in all_libraries
        if lib['name'].lower() in wanted
        or slug_library_name(lib['name']).lower() in wanted
        or normalize_library_query(lib['name']) in wanted_slugs
    ]
    if not selected:
        raise NameError(f"No libraries found named: {lib_list}")
    return selected


def resolve_library_name(cli_libraries=None, default=''):
    """CLI --library list (repeatable or comma-separated), else default (empty = all)."""
    if cli_libraries:
        names = []
        for item in cli_libraries:
            names.extend(split_library_names(item))
        return ','.join(names)
    return default


def add_library_argument(parser, extra_help='Default: all individual libraries.'):
    """Add --library to an ArgumentParser (repeatable, comma-separated)."""
    parser.add_argument(
        '--library',
        action='append',
        dest='libraries',
        metavar='NAME',
        help='ADS library to export. Repeat for several, or comma-separate. '
             + extra_help,
    )


def export_bibcodes(bibcodes, headers, export_format='bibtexabs',
                    keyformat='%1H%R', sort_format='first_author asc',
                    fix_journal=True):
    """Export bibcodes via the ADS export API, returning parsed records."""
    if not bibcodes:
        return {}
    export_url = "https://api.adsabs.harvard.edu/v1/export/" + export_format
    rows = 2000
    records = {}
    for start in range(0, len(bibcodes), rows):
        chunk = bibcodes[start:start + rows]
        response = requests.request(
            "POST",
            export_url,
            headers=headers,
            data=json.dumps({
                "bibcode": chunk,
                "keyformat": keyformat,
                "sort": sort_format,
            }),
        )
        payload = response.json()
        if 'export' not in payload:
            raise ValueError(payload)
        temp_bib = adsresponse_to_dict(payload['export'])
        if fix_journal:
            temp_bib = fix_journal_abbr(temp_bib, format='short')
        records.update(temp_bib)
    return records


def _is_bib_entry_start(text, index):
    """True if text[index] is '@' starting a BibTeX record (@TYPE{key)."""
    if index >= len(text) or text[index] != '@':
        return False
    pos = index + 1
    if pos >= len(text) or not text[pos].isalpha():
        return False
    while pos < len(text) and text[pos].isalpha():
        pos += 1
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos < len(text) and text[pos] == '{'


def split_bib_records(bib_text):
    """Split a .bib blob into records. Ignores '@' inside braces (e.g. abstracts)."""
    records = []
    start = None
    depth = 0
    pos = 0
    length = len(bib_text)
    while pos < length:
        char = bib_text[pos]
        if char == '\\' and pos + 1 < length:
            pos += 2
            continue
        if char == '{' :
            depth += 1
        elif char == '}':
            if depth > 0:
                depth -= 1
        elif depth == 0 and _is_bib_entry_start(bib_text, pos):
            if start is not None:
                records.append(bib_text[start:pos])
            start = pos
        pos += 1
    if start is not None:
        records.append(bib_text[start:])
    return records


def _field_assignment_value(item, field):
    """Return the assigned value if this line is `field = ...`, else None.

    `title` must not match `booktitle`; `note` must not match `adsnote`.
    """
    stripped = item.lstrip()
    prefix = field + ' ='
    if stripped.startswith(prefix):
        return stripped[len(prefix):].lstrip()
    compact = field + '='
    if stripped.startswith(compact):
        return stripped[len(compact):].lstrip()
    return None


def adsresponse_to_dict(bib_received):

    list_bib = [chunk.lstrip()[1:] for chunk in split_bib_records(bib_received)]
    if not list_bib:
        return {}
    #
    # Extract abstract
    if 'abstract = ' in list_bib[0]:
        has_abstract = True
    else:
        has_abstract = False

    #bib_keys = default_solr_fields()

    # store library into 2D dictionary
    records = {}
    for record in list_bib:

        row = [r.strip() for r in record.strip().split(',\n')]

        # Replace space in author names
        ads_key = row[0].replace(' ', '-')
        #
        if ads_key == '':
            pass
        else:
            pub_type = '@'+ads_key.split('{')[0]

            try:
                field_dict = __get_fields(pub_type)
                fields = field_dict.values()
            except Exception as error:
                print(f'{pub_type} unknown')
                print("An exception occurred:", type(error).__name__, "–", error) 

            # split values into dictionary
            temp_dict = {}
            abs_loc = 0
            for field in fields:
                matched = None
                for i, item in enumerate(row):
                    value = _field_assignment_value(item, field)
                    if value is None:
                        continue
                    matched = value
                    if field.lower() == 'abstract':
                        abs_loc = i
                if matched is not None:
                    temp_dict[field] = matched.strip() 
            #print(len(row))
            #print(kend)
            if has_abstract == True:
                try:
                    abstract_finish = abs_loc + len(row) - len(temp_dict.keys()) 
                    
                    temp_abst = [line.split('abstract =')[-1] for line in row[abs_loc:abstract_finish]]
                    
                    abst = ' '.join(temp_abst)
                    abstract = ' '.join([ line.strip() for line in abst.split('\n') ] ) + '}"'
                    temp_dict['abstract'] = abstract.replace('}"}"','}"')
                except Exception as error:
                    print(row)
                    print("An exception occurred:", type(error).__name__, "–", error) # An exception occurred: ZeroDivisionError – division by zero

            for key, value in _bib_line_fields(record).items():
                if key not in temp_dict or not str(temp_dict.get(key) or '').strip():
                    temp_dict[key] = value
    
            records[ads_key] = OrderedDict(temp_dict)
            
    #
    return records


def _bib_line_fields(record_text):
    """Parse field = value lines from one BibTeX record (offline files)."""
    fields = OrderedDict()
    for line in record_text.split('\n')[1:]:
        stripped = line.strip().rstrip(',').strip()
        if not stripped or stripped == '}':
            continue
        if '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        key = key.strip()
        if not key or ' ' in key:
            continue
        fields[key] = value.strip()
    return fields


def fix_journal_abbr(bib_dict, format='short'):
    # 'short' prints abbreviated journal name; e.g. A&A, MNRAS, ApJ
    # 'long' prints full name; Astronomy & Astrophysics
    short_name, long_name = journal_names()
    #
    journal_dict = short_name
    if format == 'long':
        journal_dict = long_name
    #
    for item in bib_dict.keys():
        #
        try:
            e = bib_dict[item]['journal']
            #
            journal = e[1:-1] # remove '{', '}'
            if journal[0] == '\\':
                name = journal_dict[journal]
                new_name = '{' + name + '}'
                bib_dict[item]['journal'] = new_name
        except:
            pub_type = __get_fields(f'@{item.split("{")[0]}')
            values = [x.lower() for x in pub_type.values()]
            if 'journal' in values:
                warnings.warn(f"Warning: {item} has no 'Journal' keyword.")
            else:
                # 'Journal' not expected for this pub_type
                pass
    return bib_dict

def resolve_uat(code, thesaurus=None):
    # look up the keyword code corresponding to the unified thesaurus
    # https://astrothesaurus.org/
    if thesaurus is None:
        thesaurus = _load_uat()
    return thesaurus[code]
    
def add_keyword_tag(bib_dict, tag, only_myads=False):
    
    for item in bib_dict.keys():
        if only_myads:
            bib_dict[item]['keywords']= '{' + f'{tag.strip().title()}' + '}'
        else:
            if 'keywords' in bib_dict[item].keys():
                #
                keywords = bib_dict[item]['keywords'][1:-1] # remove '{', '}}
                key_str = keywords.split(',')
                #
                new_keys = []
                for k in key_str:
                    try:
                        code = int(k)
                        desc = resolve_uat(code)
                        new_keys.append(desc)
                    except:
                        new_keys.append(k.strip().title())

                # some article contain a code that resolves to existing keyword
                # remove duplicate occurancies
                new_keys = set(new_keys)
                bib_dict[item]['keywords'] = '{'+f'{",".join(new_keys)},{tag}'+'}'            
            else:
                bib_dict[item]['keywords']= '{' + f'{tag.strip().title()}' + '}'
        
    return bib_dict
    
def sanitise_multi(megalib):
    # megalib is a list of N dictionaries.
    # Find and merge multiple occurencies, keeping all tags

    if not megalib:
        return {}

    Nlibs = len(megalib)
    records = megalib[0]

    if Nlibs == 1:
        pass
    else:
        for lib in megalib[1:]:
            for lib_key, lib_value in lib.items():
                if lib_key in records.keys():
                    # merge keywords
                    # Ingore beginning and end brackets: "{},". 
                    # Don't replace them, as they can appear inside the text.
                    temp_keywords = lib[lib_key]['keywords'][1:-1].split(',')
                    old_keywords = records[lib_key]['keywords'][1:-1].split(',')
                    #
                    new_keywords = list(set(temp_keywords+old_keywords))
                    # update keywords with merged set
                    records[lib_key]['keywords'] = '{'+','.join(new_keywords)+'}'
                else:
                    records[lib_key] = lib_value
    return records


def tag_library_records(library_records, tag_prefix='', keep_only_library=False,
                        add_keyword=True):
    """Merge per-library records with ADS library names added as keywords."""
    tagged = []
    for slug, recs in library_records.items():
        chunk = copy.deepcopy(recs)
        if add_keyword:
            chunk = add_keyword_tag(
                chunk,
                tag=f'{tag_prefix}{slug}',
                only_myads=keep_only_library,
            )
        tagged.append(chunk)
    return sanitise_multi(tagged)


def dict_to_bib(records, fout, columns=''):
    # format for saving in .bib
    final_bib = ''
    for key1, value_dict in records.items():
        
        inner_str = ',\n'.join([f'{key2.rjust(16, " ")} = {value}' for key2, value in value_dict.items()])
        
        final_bib = final_bib + f'@{key1},\n{inner_str}'+'\n}\n\n'
    
    fout.write(final_bib)
    return 
    
    
def dict_to_csv(records, fout, columns=''):
    # Save .bib in .csv
    # Predefined columns, empty column if not a valid .bib field.
    import csv

    write = csv.writer(fout)

    # CSV header
    write.writerow(['No'] + columns)

    # Select columns, add extras
    entries = []
    for i, rec_k in enumerate(records):
        entry = [i+1]
        # rec_k = citation_key
        # records[rec_k] = dictionary with bibtex record
        for column in columns:
            if column == 'citekey':
                entry.append(rec_k.split('{')[-1])
            elif column in records[rec_k]:
                value = records[rec_k][column].replace('{','').replace('}','')
                if column == 'doi':
                    value = f'https://doi.org/{value}'   
                entry.append(value)
            else:
                if column == 'read status':
                    value = 'false'
                elif column == 'relevance':
                    value = 'false'
                else:
                    value = ''
                entry.append(value)

        entries.append(entry)

    write.writerows(entries)
    
    return


ADS_ABSTRACT_START = '<!-- ads-abstract -->'
ADS_BODY_MARKER = '<!-- ads-body -->'
USER_NOTE_KEYS = ('read_status', 'relevance', 'pdf')
CATALOGUE_NOTE_KEYS = (
    'citekey', 'title', 'year', 'author', 'journal', 'doi', 'eprint',
    'adsurl', 'keywords', 'collections', 'tags',
)


_TEX_ACCENTS = {
    "'": {
        'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú', 'y': 'ý',
        'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú', 'Y': 'Ý',
        'c': 'ć', 'C': 'Ć', 'n': 'ń', 's': 'ś', 'z': 'ź',
    },
    '"': {
        'a': 'ä', 'e': 'ë', 'i': 'ï', 'o': 'ö', 'u': 'ü', 'y': 'ÿ',
        'A': 'Ä', 'E': 'Ë', 'I': 'Ï', 'O': 'Ö', 'U': 'Ü',
    },
    '`': {
        'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù',
        'A': 'À', 'E': 'È', 'I': 'Ì', 'O': 'Ò', 'U': 'Ù',
    },
    '^': {
        'a': 'â', 'e': 'ê', 'i': 'î', 'o': 'ô', 'u': 'û',
        'A': 'Â', 'E': 'Ê', 'I': 'Î', 'O': 'Ô', 'U': 'Û',
    },
    '~': {
        'a': 'ã', 'n': 'ñ', 'o': 'õ', 'A': 'Ã', 'N': 'Ñ', 'O': 'Õ',
    },
}
_TEX_V = {'s': 'š', 'S': 'Š', 'z': 'ž', 'Z': 'Ž', 'c': 'č', 'C': 'Č',
          'r': 'ř', 'n': 'ň', 'e': 'ě'}
_TEX_C = {'c': 'ç', 'C': 'Ç'}
_TEX_DOT = {'z': 'ż', 'Z': 'Ż'}


def _braces_wrap_whole(text):
    if not (text.startswith('{') and text.endswith('}')):
        return False
    depth = 0
    for i, char in enumerate(text):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return i == len(text) - 1
            if depth < 0:
                return False
    return False


def decode_tex_accents(text):
    """Turn common BibTeX/TeX accent commands into Unicode."""
    import re
    text = re.sub(r'\{\\ensuremath\{\\mu\}\}', 'μ', text)
    text = re.sub(r'\{\\mu\}', 'μ', text)
    text = re.sub(r'\\ensuremath\{\\mu\}', 'μ', text)
    text = re.sub(r'\{\\times\}', '×', text)
    text = re.sub(r'\{\\sim\}', '∼', text)
    text = re.sub(r'\{\\pm\}', '±', text)
    text = re.sub(r'\{\\infty\}', '∞', text)
    text = re.sub(r'\{\\aa\}', 'å', text)
    text = re.sub(r'\{\\AA\}', 'Å', text)
    text = re.sub(r'\{\\o\}', 'ø', text)
    text = re.sub(r'\{\\O\}', 'Ø', text)
    text = re.sub(r'\{\\ae\}', 'æ', text)
    text = re.sub(r'\{\\AE\}', 'Æ', text)
    text = re.sub(r'\{\\ss\}', 'ß', text)
    text = re.sub(r'\{\\l\}', 'ł', text)
    text = re.sub(r'\{\\L\}', 'Ł', text)
    text = re.sub(r"\{\\'\\i\}", 'í', text)
    text = re.sub(r"\{\\'i\}", 'í', text)
    text = re.sub(r"\\'\\i", 'í', text)

    def _umlaut(match):
        return _TEX_ACCENTS['"'].get(match.group(1), match.group(1))

    text = re.sub(r'\{\{\\"([A-Za-z])\}', _umlaut, text)
    text = re.sub(r'\{\\"([A-Za-z])\}', _umlaut, text)
    text = re.sub(r'\\"([A-Za-z])', _umlaut, text)

    for marker, table in _TEX_ACCENTS.items():
        escaped = re.escape(marker)

        def _sub(match, mapping=table):
            return mapping.get(match.group(1), match.group(1))

        text = re.sub(r'\{\\' + escaped + r'\{([A-Za-z])\}\}', _sub, text)
        text = re.sub(r'\{\\' + escaped + r'([A-Za-z])\}', _sub, text)
        text = re.sub(r'\\' + escaped + r'\{([A-Za-z])\}', _sub, text)
        text = re.sub(r'\\' + escaped + r'([A-Za-z])', _sub, text)

    def _v(match):
        return _TEX_V.get(match.group(1), match.group(1))

    def _c(match):
        return _TEX_C.get(match.group(1), match.group(1))

    def _dot(match):
        return _TEX_DOT.get(match.group(1), match.group(1))

    text = re.sub(r'\{\\v\{([A-Za-z])\}\}', _v, text)
    text = re.sub(r'\\v\{([A-Za-z])\}', _v, text)
    text = re.sub(r'\{\\c\{([A-Za-z])\}\}', _c, text)
    text = re.sub(r'\\c\{([A-Za-z])\}', _c, text)
    text = re.sub(r'\{\\\.\{([A-Za-z])\}\}', _dot, text)
    text = re.sub(r'\\\.\{([A-Za-z])\}', _dot, text)
    return text


def clean_bib_text(value):
    """Plain-text Obsidian property from a BibTeX/ADS field."""
    import re
    if value is None:
        return ''
    text = str(value).strip()
    for _ in range(12):
        prev = text
        if _braces_wrap_whole(text):
            inner = text[1:-1]
            if '{' not in inner:
                text = inner.strip()
        elif len(text) >= 2 and text[0] == text[-1] and text[0] in '"\'':
            text = text[1:-1].strip()
        if text.startswith('"{'):
            text = text[2:].strip()
        elif text.startswith('"') and text.count('"') == 1:
            text = text[1:].strip()
        elif text.startswith("'") and text.count("'") == 1:
            text = text[1:].strip()
        if text.startswith('{') and text.count('{') > text.count('}'):
            text = text[1:].strip()
        if text.endswith('}"') and text.count('{') < text.count('}'):
            text = text[:-2].strip()
        elif text.endswith('}') and text.count('}') > text.count('{'):
            text = text[:-1].strip()
        elif text.endswith('"') and text.count('"') == 1:
            text = text[:-1].strip()
        if text == prev:
            break
    text = decode_tex_accents(text)
    for _ in range(8):
        nxt = re.sub(r'\{([^{}]+)\}', r'\1', text)
        if nxt == text:
            break
        text = nxt
    text = text.replace('{', '').replace('}', '')
    text = text.replace('~', ' ')
    text = text.replace('\\&', '&')
    text = re.sub(r'\\+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def strip_bib_braces(value):
    """Remove wrapping BibTeX braces/quotes from a field value."""
    return clean_bib_text(value)


def keyword_terms_from_record(record):
    """Human-readable keyword list; numeric UAT codes are resolved when possible."""
    raw = record.get('keywords', '') if isinstance(record, dict) else record
    if isinstance(raw, (list, tuple)):
        terms = []
        for item in raw:
            terms.extend(keyword_terms_from_record({'keywords': item}))
        return _unique_keep_order(terms)
    text = clean_bib_text(raw)
    terms = []
    for part in text.split(','):
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            try:
                terms.append(resolve_uat(int(part)))
            except Exception:
                pass
            continue
        terms.append(part)
    return _unique_keep_order(terms)


def _unique_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def obsidian_tag(text):
    """Filesystem-safe Obsidian tag (no spaces)."""
    import re
    text = clean_bib_text(text)
    text = text.replace(' ', '-').replace('_', '-')
    text = re.sub(r'-+', '-', text)
    text = re.sub(r'[^\w./-]', '', text, flags=re.UNICODE)
    return text.strip('-')


def ads_library_tag(library_name, tag_prefix=''):
    """ADS library tag, same slug rule as tag.py."""
    slug = library_name.replace(' ', '-').replace('_', '-')
    return obsidian_tag(f'{tag_prefix}{slug}')


def vault_tags(collections, keyword_list=None, tag_prefix='', keep_only_library=False):
    """Obsidian tags: ADS library names, plus keyword tags unless library-only."""
    tags = []
    seen = set()

    def add(value):
        tag = obsidian_tag(value)
        if not tag:
            return
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            tags.append(tag)

    for coll in collections or []:
        add(ads_library_tag(coll, tag_prefix))
    if not keep_only_library:
        for term in keyword_list or []:
            add(term)
    return tags


def keywords_to_list(value):
    """Split a BibTeX keywords field into a YAML list."""
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(keywords_to_list(item))
        return items
    text = clean_bib_text(value)
    if not text:
        return []
    return [part.strip() for part in text.split(',') if part.strip() and not part.strip().isdigit()]


def citekey_from_ads_key(ads_key):
    return ads_key.split('{')[-1]


def safe_note_stem(citekey):
    """Filename stem for a paper note (citekey with path-unsafe characters removed)."""
    cleaned = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in citekey)
    return cleaned or 'paper'


def _yaml_scalar(value):
    if value is None:
        return '""'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    text = str(value)
    if text == '':
        return '""'
    needs_quote = (
        text != text.strip()
        or text.lower() in ('true', 'false', 'null', 'yes', 'no')
        or any(ch in text for ch in ':#{}[]&*?|>\'\"%@`\n')
        or text[:1] in '-?!'
    )
    if needs_quote:
        return json.dumps(text, ensure_ascii=False)
    return text


def dump_note_frontmatter(meta):
    """Serialize a paper note YAML block (subset of YAML)."""
    lines = ['---']
    list_keys = ('collections', 'keywords', 'tags')
    for key in CATALOGUE_NOTE_KEYS + USER_NOTE_KEYS:
        if key not in meta:
            continue
        value = meta[key]
        if key in list_keys or isinstance(value, (list, tuple)):
            lines.append(f'{key}:')
            items = value if isinstance(value, (list, tuple)) else [value]
            items = [item for item in items if item != '']
            if not items:
                lines.append('  []')
            else:
                for item in items:
                    lines.append(f'  - {_yaml_scalar(item)}')
            continue
        lines.append(f'{key}: {_yaml_scalar(value)}')
    lines.append('---')
    return '\n'.join(lines) + '\n'


def parse_note_frontmatter(text):
    """Parse the YAML-like frontmatter this module writes."""
    if not text.startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}, text
    yaml_text = parts[1].strip('\n')
    body = parts[2].lstrip('\n')
    meta = {}
    lines = yaml_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith(('collections:', 'keywords:', 'tags:')):
            key = line.split(':', 1)[0]
            rest = line.split(':', 1)[1].strip()
            items = []
            if rest and rest != '[]':
                items.append(json.loads(rest) if rest[:1] in '"[' else rest)
            i += 1
            while i < len(lines) and lines[i].startswith('  - '):
                raw = lines[i][4:].strip()
                if raw.startswith('"'):
                    items.append(json.loads(raw))
                else:
                    items.append(raw)
                i += 1
            meta[key] = items
            continue
        if ':' not in line:
            i += 1
            continue
        key, raw = line.split(':', 1)
        raw = raw.strip()
        if raw.startswith('"'):
            meta[key] = json.loads(raw)
        elif raw.lower() in ('true', 'false'):
            meta[key] = raw.lower() == 'true'
        else:
            meta[key] = raw
        i += 1
    return meta, body


def coerce_read_status(value):
    """Obsidian checkbox: true if read, false if unread."""
    if isinstance(value, bool):
        return value
    if value is None or value == '':
        return False
    text = str(value).strip().lower().strip('"')
    if text in ('true', 'yes', 'read', 'done', '1'):
        return True
    return False


def record_catalogue(ads_key, record, collections, tag_prefix='',
                     keep_only_library=False, add_tags=True):
    """Catalogue fields for YAML (safe to refresh from ADS)."""
    def field(*names):
        for name in names:
            if name in record:
                return strip_bib_braces(record[name])
        return ''

    adsurl = field('adsurl')
    if adsurl and not adsurl.startswith('http'):
        adsurl = 'https://ui.adsabs.harvard.edu/abs/' + adsurl
    doi = field('doi')
    keywords = keyword_terms_from_record(record)
    coll = list(collections)
    tags = []
    if add_tags:
        tags = vault_tags(
            coll,
            keyword_list=keywords,
            tag_prefix=tag_prefix,
            keep_only_library=keep_only_library,
        )
    return {
        'citekey': citekey_from_ads_key(ads_key),
        'title': field('title'),
        'year': field('year'),
        'author': field('author'),
        'journal': field('journal', 'booktitle', 'howpublished'),
        'doi': doi,
        'eprint': field('eprint'),
        'adsurl': adsurl,
        'keywords': keywords,
        'collections': coll,
        'tags': tags,
    }


def paper_seed_body(abstract):
    abstract = clean_bib_text(abstract)
    return (
        f'{ADS_ABSTRACT_START}\n{abstract}\n\n'
        f'{ADS_BODY_MARKER}\n'
        '## Summary\n\n'
        '## Argument\n\n'
        '## Methods\n\n'
        '## Figures\n\n'
        '## Quotes\n'
    )


def merge_note_body(existing_body, abstract):
    """Refresh the ADS abstract block; keep everything after the body marker."""
    if ADS_BODY_MARKER in existing_body:
        user_part = existing_body.split(ADS_BODY_MARKER, 1)[1]
        abstract = clean_bib_text(abstract)
        return f'{ADS_ABSTRACT_START}\n{abstract}\n\n{ADS_BODY_MARKER}{user_part}'
    return existing_body


def write_paper_note(path, catalogue, abstract, existing_text=None, pdf_link=''):
    """Create or merge-update a paper note. Returns 'created' or 'updated'."""
    user_meta = {
        'read_status': False,
        'relevance': '',
        'pdf': pdf_link or '',
    }
    body = paper_seed_body(abstract)
    if existing_text:
        old_meta, old_body = parse_note_frontmatter(existing_text)
        for key in USER_NOTE_KEYS:
            if key in old_meta and old_meta[key] != '':
                user_meta[key] = old_meta[key]
        if not user_meta['pdf'] and pdf_link:
            user_meta['pdf'] = pdf_link
        user_meta['read_status'] = coerce_read_status(user_meta.get('read_status'))
        old_coll = old_meta.get('collections') or []
        if isinstance(old_coll, str):
            old_coll = [old_coll] if old_coll else []
        if not (catalogue.get('collections') or []) and old_coll:
            catalogue['collections'] = list(old_coll)
            extra = [t for t in (catalogue.get('tags') or []) if t]
            coll_tags = [slug_library_name(c) for c in old_coll]
            catalogue['tags'] = list(dict.fromkeys(coll_tags + extra))
        body = merge_note_body(old_body, abstract)
        action = 'updated'
    else:
        action = 'created'
    meta = {}
    meta.update(catalogue)
    meta.update(user_meta)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fout:
        fout.write(dump_note_frontmatter(meta))
        fout.write('\n')
        fout.write(body if body.endswith('\n') else body + '\n')
    return action


def reclean_paper_note(text):
    """Re-clean catalogue fields and abstract on an existing paper note."""
    meta, body = parse_note_frontmatter(text)
    if not meta:
        return text
    for key in ('citekey', 'title', 'author', 'journal', 'doi', 'eprint'):
        if key in meta and isinstance(meta[key], str):
            meta[key] = clean_bib_text(meta[key])
    if 'keywords' in meta:
        meta['keywords'] = keyword_terms_from_record({'keywords': meta['keywords']})
    collections = meta.get('collections') or []
    if isinstance(collections, str):
        collections = [collections]
    meta['collections'] = collections
    meta['read_status'] = coerce_read_status(meta.get('read_status'))
    meta['tags'] = vault_tags(collections, keyword_list=meta.get('keywords') or [])
    if ADS_BODY_MARKER in body:
        prefix, user_part = body.split(ADS_BODY_MARKER, 1)
        abstract = prefix.replace(ADS_ABSTRACT_START, '').strip()
        abstract = clean_bib_text(abstract)
        body = f'{ADS_ABSTRACT_START}\n{abstract}\n\n{ADS_BODY_MARKER}{user_part}'
        if not body.endswith('\n'):
            body += '\n'
    return dump_note_frontmatter(meta) + '\n' + body


def reclean_papers_dir(papers_dir):
    """Rewrite paper notes in place with cleaned catalogue text. Returns count."""
    updated = 0
    if not os.path.isdir(papers_dir):
        return updated
    for name in os.listdir(papers_dir):
        if not name.endswith('.md'):
            continue
        path = os.path.join(papers_dir, name)
        with open(path, encoding='utf-8') as fin:
            original = fin.read()
        cleaned = reclean_paper_note(original)
        if cleaned != original:
            with open(path, 'w', encoding='utf-8') as fout:
                fout.write(cleaned)
            updated += 1
    return updated


def arxiv_id_from_eprint(eprint):
    """Return an arXiv id from an eprint/doi/url string, or ''."""
    import re
    text = strip_bib_braces(eprint).strip()
    if not text:
        return ''
    doi_arxiv = re.search(r'10\.48550/arXiv\.(\d{4}\.\d{4,5})', text, re.I)
    if doi_arxiv:
        return doi_arxiv.group(1)
    url_arxiv = re.search(
        r'arxiv(?:\.org/(?:abs|pdf)/|\.org/pdf/|[.:/]+)(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[a-z]{2})?/\d{7})',
        text,
        re.I,
    )
    if url_arxiv:
        return url_arxiv.group(1)
    text = text.replace('arXiv:', '').replace('arxiv:', '').strip()
    if text.lower().startswith('10.') and 'arxiv' not in text.lower():
        return ''
    if re.fullmatch(r'\d{4}\.\d{4,5}(?:v\d+)?', text):
        return text
    if re.fullmatch(r'[a-z\-]+(?:\.[A-Za-z]{2})?/\d{7}', text, re.I):
        return text
    return ''


def arxiv_id_from_record(record, note_text=None):
    """arXiv id from a BibTeX record, then from an existing paper note."""
    blobs = [
        (record or {}).get('eprint', ''),
        (record or {}).get('doi', ''),
        (record or {}).get('adsurl', ''),
        (record or {}).get('url', ''),
    ]
    if note_text:
        meta, _ = parse_note_frontmatter(note_text)
        blobs.extend([meta.get('eprint', ''), meta.get('doi', '')])
    for blob in blobs:
        arxiv_id = arxiv_id_from_eprint(blob)
        if arxiv_id:
            return arxiv_id
    return ''


def download_arxiv_pdf(eprint, dest_path, timeout=60):
    """Download an arXiv PDF only if dest_path does not already exist."""
    if os.path.exists(dest_path):
        return False
    arxiv_id = arxiv_id_from_eprint(eprint)
    if not arxiv_id:
        return False
    headers = {
        'User-Agent': 'ads-megalib/1.0 (literature vault; +https://arxiv.org)',
        'Accept': 'application/pdf',
    }
    urls = [
        'https://arxiv.org/pdf/' + arxiv_id + '.pdf',
        'https://arxiv.org/pdf/' + arxiv_id,
        'https://export.arxiv.org/pdf/' + arxiv_id,
    ]
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + '.part'
    last_error = None
    for url in urls:
        try:
            response = requests.get(
                url, timeout=timeout, stream=True, headers=headers
            )
            response.raise_for_status()
            ctype = response.headers.get('Content-Type', '')
            if 'html' in ctype.lower():
                last_error = ValueError('arXiv returned HTML for ' + arxiv_id)
                continue
            with open(tmp_path, 'wb') as fout:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        fout.write(chunk)
            with open(tmp_path, 'rb') as fin:
                magic = fin.read(5)
            if magic != b'%PDF-':
                last_error = ValueError('Not a PDF from ' + url)
                continue
            os.replace(tmp_path, dest_path)
            return True
        except Exception as exc:
            last_error = exc
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    if last_error:
        raise last_error
    return False


def filter_records(records, citekeys=None):
    """Subset of ADS records by citekey (the part after '{')."""
    if not citekeys:
        return dict(records)
    wanted = {key.strip() for key in citekeys if key.strip()}
    return {
        ads_key: rec
        for ads_key, rec in records.items()
        if citekey_from_ads_key(ads_key) in wanted
    }


def records_from_export_csv(path):
    """Rebuild record dicts from a CSV written by export.py."""
    import csv
    records = {}
    with open(path, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            citekey = (row.get('citekey') or '').strip()
            if not citekey:
                continue
            ads_key = 'ARTICLE{' + citekey
            rec = OrderedDict()
            doi = (row.get('doi') or '').strip()
            if doi.startswith('https://doi.org/'):
                doi = doi[len('https://doi.org/'):]
            mapping = {
                'title': row.get('title', ''),
                'year': row.get('year', ''),
                'author': row.get('author', ''),
                'journal': row.get('journal', ''),
                'keywords': row.get('keywords', ''),
                'doi': doi,
                'eprint': row.get('eprint', ''),
                'adsurl': row.get('adsurl', ''),
                'abstract': row.get('abstract', ''),
            }
            for field, value in mapping.items():
                text = (value or '').strip().strip('"')
                if text:
                    rec[field] = '{' + text + '}'
            records[ads_key] = rec
    return records


def records_from_bib(path):
    """Parse a BibTeX file written by export.py, tag.py, or vault.py."""
    with open(path, encoding='utf-8') as fin:
        return adsresponse_to_dict(fin.read())


def membership_by_citekey(collections_by_key):
    """Map citekey -> collection slugs (merges variant ADS keys for one paper)."""
    out = {}
    for ads_key, colls in (collections_by_key or {}).items():
        cite = citekey_from_ads_key(ads_key)
        bucket = out.setdefault(cite, [])
        for coll in colls or []:
            slug = slug_library_name(coll) if coll else ''
            if slug and slug not in bucket:
                bucket.append(slug)
    return out


def collections_for_record(ads_key, collections_by_key):
    """Collection slugs for one record, matching on citekey if needed."""
    if ads_key in (collections_by_key or {}):
        found = [c for c in collections_by_key[ads_key] if c]
        if found:
            return found
    return membership_by_citekey(collections_by_key).get(
        citekey_from_ads_key(ads_key), []
    )


def records_and_collections_from_dir(collections_dir, skip_names=None):
    """Load bib/collections/<slug>.bib → library_records and collections_by_key."""
    library_records = OrderedDict()
    collections_by_key = {}
    if not collections_dir or not os.path.isdir(collections_dir):
        return library_records, collections_by_key
    for name in sorted(os.listdir(collections_dir)):
        if not name.endswith('.bib'):
            continue
        slug = name[:-4]
        if not slug or is_union_library_name(slug, skip_names):
            continue
        recs = records_from_bib(os.path.join(collections_dir, name))
        library_records[slug] = recs
        for ads_key in recs:
            collections_by_key.setdefault(ads_key, [])
            if slug not in collections_by_key[ads_key]:
                collections_by_key[ads_key].append(slug)
    return library_records, collections_by_key


def merge_collection_maps(*maps):
    """Union collection membership dicts, matching papers by citekey."""
    merged = {}
    cite_to_key = {}
    for mapping in maps:
        for ads_key, colls in (mapping or {}).items():
            cite = citekey_from_ads_key(ads_key)
            target = cite_to_key.get(cite, ads_key)
            cite_to_key[cite] = target
            bucket = merged.setdefault(target, [])
            for coll in colls or []:
                if not coll:
                    continue
                slug = slug_library_name(coll)
                if slug and slug not in bucket:
                    bucket.append(slug)
    return merged


def drop_union_collections(collections_by_key, skip_names=None):
    """Remove MEGALIB (and other skip_names) from collection membership."""
    skip = union_library_slugs(skip_names)
    out = {}
    for ads_key, colls in (collections_by_key or {}).items():
        kept = []
        for coll in colls or []:
            if not coll:
                continue
            slug = slug_library_name(coll)
            if slug.lower() in skip or coll.lower() in skip:
                continue
            if slug not in kept:
                kept.append(slug)
        out[ads_key] = kept
    return out


def library_records_from_membership(all_records, collections_by_key):
    """Rebuild per-collection record dicts from membership + catalogue records."""
    by_cite = {
        citekey_from_ads_key(key): (key, rec) for key, rec in (all_records or {}).items()
    }
    library_records = OrderedDict()
    for ads_key, colls in (collections_by_key or {}).items():
        cite = citekey_from_ads_key(ads_key)
        if ads_key in (all_records or {}):
            key, rec = ads_key, all_records[ads_key]
        elif cite in by_cite:
            key, rec = by_cite[cite]
        else:
            continue
        for coll in colls or []:
            slug = slug_library_name(coll)
            if not slug:
                continue
            library_records.setdefault(slug, OrderedDict())[key] = rec
    return library_records


def _records_by_citekey(records):
    return {citekey_from_ads_key(key): (key, rec) for key, rec in records.items()}


def _keyword_match_key(term):
    return obsidian_tag(term).lower()


def merge_plain_and_tagged(plain_records, tagged_records, skip_names=None):
    """Catalogue from library.bib; collections from extra keywords in library_tagged.bib.

    Returns library_records, all_records, collections_by_key.
    skip_names (e.g. MEGALIB) are never treated as collections.
    """
    plain_index = _records_by_citekey(plain_records or {})
    tagged_index = _records_by_citekey(tagged_records or {})
    citekeys = list(dict.fromkeys([*plain_index, *tagged_index]))

    all_records = OrderedDict()
    collections_by_key = {}
    library_records = OrderedDict()

    for citekey in citekeys:
        plain_key, plain_rec = plain_index.get(citekey, (None, {}))
        tagged_key, tagged_rec = tagged_index.get(citekey, (None, {}))
        ads_key = plain_key or tagged_key
        rec = OrderedDict()
        rec.update(tagged_rec)
        rec.update(plain_rec)
        if tagged_rec.get('abstract'):
            rec['abstract'] = tagged_rec['abstract']
        if plain_rec.get('keywords'):
            rec['keywords'] = plain_rec['keywords']
        all_records[ads_key] = rec

        plain_terms = keyword_terms_from_record(plain_rec) if plain_rec else []
        tagged_terms = keyword_terms_from_record(tagged_rec) if tagged_rec else []
        plain_keys = {_keyword_match_key(term) for term in plain_terms}
        collections = []
        if tagged_rec and plain_rec:
            for term in tagged_terms:
                if _keyword_match_key(term) not in plain_keys:
                    slug = slug_library_name(term)
                    if slug and not is_union_library_name(slug, skip_names):
                        if slug not in collections:
                            collections.append(slug)
        collections_by_key[ads_key] = collections
        for slug in collections:
            library_records.setdefault(slug, OrderedDict())[ads_key] = rec

    return library_records, all_records, collections_by_key

    
    
