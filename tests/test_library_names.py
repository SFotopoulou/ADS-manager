import unittest

from core import (
    collection_bib_stem,
    is_union_library_name,
    normalize_library_query,
    resolve_library_name,
    select_libraries,
    slug_is_wanted,
    slug_library_name,
    split_library_names,
    wanted_library_slugs,
)
from tests.support import ADS_LIBRARIES


class LibraryNameTests(unittest.TestCase):
    def test_split_strips_quotes_and_spaces(self):
        self.assertEqual(
            split_library_names("jades,lesnes,'dark matter'"),
            ['jades', 'lesnes', 'dark matter'],
        )
        self.assertEqual(
            split_library_names('"dark matter",JADES'),
            ['dark matter', 'JADES'],
        )

    def test_wanted_slugs_for_user_cli(self):
        wanted = wanted_library_slugs("jades,lesnes,'dark matter'")
        self.assertEqual(wanted, {'jades', 'lesnes', 'dark-matter'})
        self.assertTrue(slug_is_wanted('JADES', wanted))
        self.assertTrue(slug_is_wanted('LESNeS', wanted))
        self.assertTrue(slug_is_wanted('dark matter', wanted))
        self.assertTrue(slug_is_wanted('dark-matter', wanted))
        self.assertFalse(slug_is_wanted('MEGALIB', wanted))

    def test_select_libraries_matches_quoted_dark_matter(self):
        selected = select_libraries(
            ADS_LIBRARIES, "jades,lesnes,'dark matter'", skip_names=['MEGALIB']
        )
        names = [lib['name'] for lib in selected]
        self.assertEqual(names, ['JADES', 'LESNeS', 'dark matter'])

    def test_default_select_skips_megalib(self):
        selected = select_libraries(ADS_LIBRARIES, '', skip_names=['MEGALIB'])
        names = [lib['name'] for lib in selected]
        self.assertEqual(names, ['JADES', 'LESNeS', 'dark matter'])
        self.assertFalse(is_union_library_name('JADES', ['MEGALIB']))
        self.assertTrue(is_union_library_name('MEGALIB', ['MEGALIB']))

    def test_explicit_megalib_is_kept(self):
        selected = select_libraries(ADS_LIBRARIES, 'MEGALIB', skip_names=['MEGALIB'])
        self.assertEqual([lib['name'] for lib in selected], ['MEGALIB'])

    def test_resolve_cli_list(self):
        self.assertEqual(
            resolve_library_name(["jades,lesnes,'dark matter'"]),
            'jades,lesnes,dark matter',
        )
        self.assertEqual(
            resolve_library_name(['jades', 'lesnes', 'dark matter']),
            'jades,lesnes,dark matter',
        )

    def test_collection_filename(self):
        self.assertEqual(collection_bib_stem('dark matter'), 'dark-matter')
        self.assertEqual(collection_bib_stem('JADES'), 'JADES')
        self.assertEqual(collection_bib_stem('LESNeS'), 'LESNeS')
        self.assertEqual(slug_library_name('dark matter'), 'dark-matter')
        self.assertEqual(normalize_library_query("'dark matter'"), 'dark-matter')


if __name__ == '__main__':
    unittest.main()
