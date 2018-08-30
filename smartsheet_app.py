import argparse
import os
import smartsheet
import sqlite3
import yaml


class Column(object):
    def __init__(self, column, column_mapping):
        self.title = column.title
        self.type = column.type
        self.data = ''
        self.ss_name = column_mapping['ss_col_name']
        self.db_name = column_mapping['db_col_name']


class Sheet(object):
    def __init__(self, config):
        self.columns = []
        self.columns_list = [mp['ss_col_name'] for mp in config['mappings']]
        self.db_file = config['db_file']
        self.mappings = config['mappings']
        self.name = config['sheet_name']
        self.table = self.name.replace(' ', '_')
        self.token = config['access_token']

    @property
    def column_strs(self):
        return ', '.join(col.db_name for col in self.columns)

    def get_columns(self):
        for column_mapping in self.mappings:
            try:
                column = next(
                    col for col in self.sheet.columns
                    if column_mapping['ss_col_name'] == col.title
                )
            except StopIteration:
                pass
            else:
                self.columns.append(Column(column, column_mapping))

    def pull(self):
        """Find and parse specified sheet via smartsheet api.
        Args:
            config (dict): Parsed .yml file.
        Returns:
            Sheet object based on name given in .yml attribute 'sheet_name'.
        """
        ss_client = smartsheet.Smartsheet(self.token)
        ss_client.errors_as_exceptions(True)
        sheets = ss_client.Sheets.list_sheets(include_all=True).data
        try:
            self.id = next(
                sheet.id for sheet in sheets if sheet.name == self.name
            )
        except StopIteration:
            raise SystemExit('Sheet {} was not found'.format(self.name))
        else:
            self.sheet = ss_client.Sheets.get_sheet(self.id)
            self.get_columns()


def process_yml(path):
    """Pull yml from config file with slight preventitive measures.
    Args:
        path (str): Path to config file.
    Returns:
        Dictionary gleaned from config.yml
    Raises:
        RuntimeError: Raise if path to config file is nonexistant.
        RuntimeError: Raise if file is incorrect.
    """
    if not path:
        raise RuntimeError('Missing path to config.yml')
    elif not os.path.isfile(path) or os.path.basename(path) != 'config.yml':
        raise RuntimeError('Incorrect path: {}'.format(path))
    with open(path, 'r') as f:
        config = yaml.load(f)
    return Sheet(config)


def to_sql(sheet):
    """Produce sqlite database from smartsheet columns.
    Args:
        sheet (Sheet): Sheet object based on name given in .yml attribute
            'sheet_name'.
        config (dict): Parsed .yml file.
    """
    conn = sqlite3.connect(sheet.db_file)
    conn = conn.cursor()
    conn.execute('CREATE TABLE {} ({})'.format(sheet.table, sheet.column_strs))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run SmartSheet script.')
    parser.add_argument(
        '--config',
        metavar='PATH',
        type=str,
        help='Path from current directory to config.yml'
    )
    args = parser.parse_args()
    sheet = process_yml(args.config)
    sheet.pull()
    to_sql(sheet)
