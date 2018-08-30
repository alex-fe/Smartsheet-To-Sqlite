import unittest
from unittest.mock import Mock

from smartsheet_app import (COLUMN_TYPES, filter_cols, process_yml)


class TestProcessYML(unittest.TestCase):
    def test_errors(self):
        """Test that RuntimeErrors are raised if the path given is incorrect.
        """
        # if path is false
        with self.assertRaises(RuntimeError):
            process_yml('')
        # if path does not lead to config.yml
        with self.assertRaises(RuntimeError):
            process_yml('./config.yl')


class TestSmartSheet(unittest.TestCase):
    pass


class TestToSQL(unittest.TestCase):

    def setUp(self):
        self.config = {
            'sheet_name': 'The Sheet Name',
            'mappings': [
                {
                    'db_col_name': 'a_db_col_name_a',
                    'ss_col_name': 'A Column Name A'
                },
                {
                    'db_col_name': 'a_db_col_name_b',
                    'ss_col_name': 'A Column Name B'
                }
            ],
            'db_file': './test.sqlite'
        }
        self.sheet = Mock()
        self.sheet.configure_mock(name=self.config['sheet_name'])
        columns = []
        for i in range(5):
            if i < len(self.config['mappings']):
                title = self.config['mappings'][i]['ss_col_name']
            else:
                title = 'Column {}'.format(i)
            col = Mock()
            col.configure_mock(title=title)
            col.configure_mock(type=list(COLUMN_TYPES.keys())[i])
            columns.append(col)
        self.sheet.configure_mock(columns=columns)

    def test_filter_cols(self):
        columns = filter_cols(self.sheet.columns, self.config['mappings'])
        correct_names = [t['ss_col_name'] for t in self.config['mappings']]
        self.assertEqual(len(list(columns)), len((self.config['mappings'])))
        for col in columns:
            self.assertIn(col.title, correct_names)


if __name__ == '__main__':
    unittest.main()
