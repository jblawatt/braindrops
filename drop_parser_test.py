
import unittest

from datetime import date
from drop_parser import DropParserManager


class DropParserTestCase(unittest.TestCase):

    def test__manager(self):
        mgr = DropParserManager([
            'drop_parser.TagParser',
            'drop_parser.BirthdayAttrParser'])

        drop = mgr.parse("hello #world @bday:20.11.1985")

        tags = drop['tags']
        attrs = drop['attrs']

        self.assertEqual(tags, {'world'})
        self.assertEqual(attrs['bday'], date(1985, 11, 20))


