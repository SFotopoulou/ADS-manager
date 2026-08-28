import os
import tempfile
import unittest
from unittest.mock import patch

from core import (
    library_records_from_membership,
    parse_note_frontmatter,
    records_from_bib,
    wanted_library_slugs,
)
from tests.support import (
    ADS_LIBRARIES,
    collection_bibs,
    fake_export_bibcodes,
    fake_get_library,
)
import vault


def _patch_ads():
    return (
        patch.object(vault, 'token_available', return_value=True),
        patch.object(vault, 'ads_auth_headers', return_value={'Authorization': 'Bearer x'}),
        patch.object(vault, 'biblib_config', return_value={'headers': {}, 'url': ''}),
        patch.object(vault, 'list_libraries', return_value=list(ADS_LIBRARIES)),
        patch.object(vault, 'get_library', side_effect=fake_get_library),
        patch.object(vault, 'export_bibcodes', side_effect=fake_export_bibcodes),
    )


class WriteCatalogueBibsTests(unittest.TestCase):
    def test_writes_collection_files_from_membership_if_library_records_empty(self):
        ads_key = 'ARTICLE{Alpha2020ApJ'
        all_records = {ads_key: {'title': '{Alpha}', 'year': '2020'}}
        collections_by_key = {ads_key: ['JADES', 'dark-matter']}
        with tempfile.TemporaryDirectory() as tmp:
            wrote = vault.write_catalogue_bibs(
                tmp, {}, all_records, '', False, collections_by_key
            )
            self.assertCountEqual(wrote, ['JADES', 'dark-matter'])
            self.assertEqual(
                collection_bibs(tmp), ['JADES.bib', 'dark-matter.bib']
            )
            jades = records_from_bib(os.path.join(tmp, 'bib', 'collections', 'JADES.bib'))
            self.assertEqual(len(jades), 1)

    def test_skips_megalib_collection_file(self):
        ads_key = 'ARTICLE{Alpha2020ApJ'
        all_records = {ads_key: {'title': '{Alpha}', 'year': '2020'}}
        library_records = {
            'MEGALIB': all_records,
            'JADES': all_records,
        }
        collections_by_key = {ads_key: ['MEGALIB', 'JADES']}
        with tempfile.TemporaryDirectory() as tmp:
            vault.write_catalogue_bibs(
                tmp, library_records, all_records, '', False, collections_by_key
            )
            self.assertEqual(collection_bibs(tmp), ['JADES.bib'])


class VaultMainCollectionTests(unittest.TestCase):
    def setUp(self):
        self._patches = _patch_ads()
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def test_library_flag_writes_one_bib_per_named_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault.main(
                cli_vault=tmp,
                cli_libraries=["jades,lesnes,'dark matter'"],
            )
            names = collection_bibs(tmp)
            self.assertEqual(names, ['JADES.bib', 'LESNeS.bib', 'dark-matter.bib'])
            self.assertNotIn('MEGALIB.bib', names)

            jades = records_from_bib(os.path.join(tmp, 'bib', 'collections', 'JADES.bib'))
            lesnes = records_from_bib(os.path.join(tmp, 'bib', 'collections', 'LESNeS.bib'))
            dm = records_from_bib(os.path.join(tmp, 'bib', 'collections', 'dark-matter.bib'))
            self.assertEqual(len(jades), 2)
            self.assertEqual(len(lesnes), 1)
            self.assertEqual(len(dm), 2)

            papers = os.path.join(tmp, 'papers')
            notes = [n for n in os.listdir(papers) if n.endswith('.md')]
            self.assertEqual(len(notes), 4)
            delta = os.path.join(papers, 'Delta2023ApJ.md')
            with open(delta, encoding='utf-8') as fin:
                meta, _ = parse_note_frontmatter(fin.read())
            self.assertCountEqual(meta['collections'], ['JADES', 'dark-matter'])

    def test_default_skips_megalib_but_still_writes_individual_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault.main(cli_vault=tmp, cli_libraries=None)
            names = collection_bibs(tmp)
            self.assertEqual(names, ['JADES.bib', 'LESNeS.bib', 'dark-matter.bib'])
            self.assertNotIn('MEGALIB.bib', names)

    def test_membership_rebuild_matches_ads_keys(self):
        library_records, all_records, collections_by_key = vault.load_from_ads(
            "jades,lesnes,'dark matter'"
        )
        self.assertCountEqual(
            list(library_records), ['JADES', 'LESNeS', 'dark-matter']
        )
        rebuilt = library_records_from_membership(all_records, collections_by_key)
        self.assertCountEqual(list(rebuilt), list(library_records))
        self.assertEqual(len(all_records), 4)


class OfflineVaultTests(unittest.TestCase):
    def test_offline_prefers_vault_bib_over_cwd_library_bib(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_bib = os.path.join(tmp, 'bib')
            os.makedirs(vault_bib, exist_ok=True)
            vault_lib = os.path.join(vault_bib, 'library.bib')
            vault_tagged = os.path.join(vault_bib, 'library_tagged.bib')
            with open(vault_lib, 'w', encoding='utf-8') as fout:
                fout.write('vault-plain\n')
            with open(vault_tagged, 'w', encoding='utf-8') as fout:
                fout.write('vault-tagged\n')
            found_lib, found_tagged = vault.find_offline_bib_paths(tmp)
            self.assertEqual(os.path.abspath(found_lib), os.path.abspath(vault_lib))
            self.assertEqual(os.path.abspath(found_tagged), os.path.abspath(vault_tagged))

    def test_offline_main_writes_collection_bibs_from_tagged_keywords(self):
        from core import dict_to_bib

        ads_key = 'ARTICLE{Alpha2020ApJ'
        plain = {ads_key: {'title': '{Alpha}', 'year': '2020', 'keywords': '{galaxies}'}}
        tagged = {
            ads_key: {
                'title': '{Alpha}',
                'year': '2020',
                'keywords': '{galaxies,JADES}',
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, 'bib'), exist_ok=True)
            with open(os.path.join(tmp, 'bib', 'library.bib'), 'w', encoding='utf-8') as fout:
                dict_to_bib(plain, fout)
            with open(
                os.path.join(tmp, 'bib', 'library_tagged.bib'), 'w', encoding='utf-8'
            ) as fout:
                dict_to_bib(tagged, fout)
            with patch.object(vault, 'token_available', return_value=False):
                with patch.object(vault, 'offline_library_bib', ''):
                    with patch.object(vault, 'offline_tagged_bib', ''):
                        vault.main(cli_vault=tmp, force_offline=True)
            self.assertIn('JADES.bib', collection_bibs(tmp))


class CliTests(unittest.TestCase):
    def test_parse_library_comma_list_with_quotes(self):
        argv = [
            'vault.py',
            '--vault',
            '/tmp/vault',
            '--library',
            "jades,lesnes,'dark matter'",
        ]
        with patch('sys.argv', argv):
            args = vault.parse_args()
        selected = vault.resolve_library_name(args.libraries, '')
        self.assertEqual(selected, 'jades,lesnes,dark matter')
        self.assertEqual(
            wanted_library_slugs(selected),
            {'jades', 'lesnes', 'dark-matter'},
        )


if __name__ == '__main__':
    unittest.main()
