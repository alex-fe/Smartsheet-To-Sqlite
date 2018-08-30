import unittest
from unittest.mock import Mock

from smartsheet_app import (
    COLUMN_TYPES, create_sql_command, filter_cols, process_yml
)


class TestProcessYML(unittest.TestCase):

    def setUp(self):
        self.path = './config.yml'

    def test_errors(self):
        """Test that RuntimeErrors are raised if the path given is incorrect.
        """
        # if path is false
        with self.assertRaises(RuntimeError):
            process_yml('')
        # if path does not lead to config.yml
        with self.assertRaises(RuntimeError):
            process_yml(self.path[:-2])

    def test_mappings_order(self):
        """Test that the columns in the config are in alphabetical order."""
        config = process_yml(self.path)
        self.assertTrue(
            all(
                x['ss_col_name'] <= y['ss_col_name']
                for x, y in zip(config['mappings'], config['mappings'][1:])
            )
        )


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
        """Assert that all columns not indicated in the .yml are excluded."""
        columns = filter_cols(self.sheet.columns, self.config['mappings'])
        correct_names = [t['ss_col_name'] for t in self.config['mappings']]
        self.assertEqual(len(list(columns)), len((self.config['mappings'])))
        for col in columns:
            self.assertIn(col.title, correct_names)

    def test_create_sql_command(self):
        message = create_sql_command(self.sheet, self.config)
        # assert table name is included
        self.assertIn(self.sheet.name.replace(' ', '_'), message)
        # assert columns are accounted for
        for col in self.config['mappings']:
            self.assertIn(col['db_col_name'], message)


if __name__ == '__main__':
    unittest.main()
