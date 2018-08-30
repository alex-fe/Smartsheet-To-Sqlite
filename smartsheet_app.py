import argparse
import os
import pandas as pd
import smartsheet
import yaml

from sqlalchemy import create_engine


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
        self.db_file = config['db_file']
        self.db_dir = os.path.dirname(self.db_file)
        self.mappings = config['mappings']
        self.name = config['sheet_name']
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
            ss_client.Sheets.get_sheet_as_csv(self.id, self.db_dir)

    def to_sql(self):
        """Produce sqlite database from smartsheet columns."""
        table = self.name.replace(' ', '_')
        csv_name = '{}/{}.csv'.format(self.db_dir, self.name)
        engine = create_engine('sqlite:///{}'.format(self.db_file), echo=False)
        df = pd.read_csv(csv_name)
        df.drop(['B', 'C'], axis=1, inplace=True)
        df.rename(
            columns={
                mapping['ss_col_name']: mapping['db_col_name']
                for mapping in self.mappings
            },
            inplace=True
        )
        df.to_sql(table, engine, if_exists='append', index=False)
        os.remove(csv_name)


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
    sheet.to_sql()
