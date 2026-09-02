import os
import tempfile
import unittest

from core import (
    coerce_read_status,
    dump_note_frontmatter,
    parse_note_frontmatter,
    write_paper_note,
)


class ReadStatusCheckboxTests(unittest.TestCase):
    def test_coerce_legacy_unread_string(self):
        self.assertFalse(coerce_read_status('unread'))
        self.assertFalse(coerce_read_status(False))
        self.assertTrue(coerce_read_status(True))
        self.assertTrue(coerce_read_status('read'))

    def test_dump_parse_boolean(self):
        text = dump_note_frontmatter({
            'citekey': 'A2020',
            'title': 'T',
            'year': '2020',
            'author': '',
            'journal': '',
            'doi': '',
            'eprint': '',
            'adsurl': '',
            'keywords': [],
            'collections': [],
            'tags': [],
            'read_status': False,
            'relevance': '',
            'pdf': '',
        })
        self.assertIn('read_status: false', text)
        meta, _ = parse_note_frontmatter(text)
        self.assertIs(meta['read_status'], False)

    def test_write_migrates_unread_string(self):
        existing = (
            '---\n'
            'citekey: A2020\n'
            'title: T\n'
            'read_status: unread\n'
            'relevance: ""\n'
            'pdf: ""\n'
            '---\n'
            '<!-- ads-abstract -->\n\n'
            '<!-- ads-body -->\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'A2020.md')
            write_paper_note(
                path,
                {'citekey': 'A2020', 'title': 'T', 'collections': [], 'tags': []},
                '',
                existing_text=existing,
            )
            with open(path, encoding='utf-8') as fin:
                out = fin.read()
        self.assertIn('read_status: false', out)
        self.assertNotIn('unread', out)


if __name__ == '__main__':
    unittest.main()
