import unittest

from core import adsresponse_to_dict, merge_plain_and_tagged, split_bib_records


PLAIN = """@ARTICLE{Alpha2020ApJ,
          title = {Alpha},
           year = 2020,
       keywords = {galaxies}
}

"""

TAGGED = """@ARTICLE{Alpha2020ApJ,
          title = {Alpha},
           year = 2020,
       keywords = {galaxies,JADES}
}

"""


class BibSplitTests(unittest.TestCase):
    def test_split_ignores_at_in_abstract(self):
        blob = (
            '@ARTICLE{A2020,\n'
            '  title = {Hello},\n'
            '  abstract = {email user@example.com and another @ mention}\n'
            '}\n'
        )
        records = split_bib_records(blob)
        self.assertEqual(len(records), 1)
        parsed = adsresponse_to_dict(blob)
        self.assertEqual(len(parsed), 1)


class MergeTaggedTests(unittest.TestCase):
    def test_extra_keyword_becomes_collection(self):
        plain = adsresponse_to_dict(PLAIN)
        tagged = adsresponse_to_dict(TAGGED)
        library_records, all_records, collections_by_key = merge_plain_and_tagged(
            plain, tagged, skip_names=['MEGALIB']
        )
        self.assertEqual(list(library_records), ['JADES'])
        self.assertEqual(len(all_records), 1)
        colls = next(iter(collections_by_key.values()))
        self.assertEqual(colls, ['JADES'])

    def test_megalib_keyword_is_not_a_collection(self):
        tagged = adsresponse_to_dict(
            TAGGED.replace('galaxies,JADES', 'galaxies,JADES,MEGALIB')
        )
        plain = adsresponse_to_dict(PLAIN)
        _, _, collections_by_key = merge_plain_and_tagged(
            plain, tagged, skip_names=['MEGALIB']
        )
        colls = next(iter(collections_by_key.values()))
        self.assertEqual(colls, ['JADES'])


class InproceedingsFieldTests(unittest.TestCase):
    def test_title_is_not_taken_from_booktitle(self):
        blob = (
            '@INPROCEEDINGS{Smith2020conf,\n'
            '          author = {Smith, A.},\n'
            '           title = {The Paper Title},\n'
            '       booktitle = {Proceedings of the Conference},\n'
            '            year = 2020\n'
            '}\n'
        )
        parsed = adsresponse_to_dict(blob)
        rec = next(iter(parsed.values()))
        self.assertIn('The Paper Title', rec['title'])
        self.assertIn('Proceedings of the Conference', rec['booktitle'])
        self.assertNotIn('Proceedings', rec['title'])
        from core import record_catalogue, strip_bib_braces
        cat = record_catalogue(next(iter(parsed)), rec, [])
        self.assertEqual(cat['title'], 'The Paper Title')
        self.assertEqual(cat['journal'], 'Proceedings of the Conference')


if __name__ == '__main__':
    unittest.main()
