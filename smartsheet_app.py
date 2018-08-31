import argparse
import os
import pandas as pd
import smartsheet
import yaml

from sqlalchemy import create_engine


class Sheet(object):
    def __init__(self, config):
        self.columns = []
        self.db_file = config['db_file']
        self.db_dir = os.path.dirname(self.db_file)
        self.mappings = config['mappings']
        self.name = config['sheet_name']
        self.token = config['access_token']

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

    def prep_table(self):
        """Create and prep DataFrame for export and removed gleaned CSV.
        Returns:
            Cleaned DataFrame.
        """
        csv_name = '{}/{}.csv'.format(self.db_dir, self.name)
        df = pd.read_csv(csv_name)
        os.remove(csv_name)
        drop_list = [
            c for c in df.columns.values.tolist()
            if c not in [mapping['ss_col_name'] for mapping in self.mappings]
        ]
        df.drop(drop_list, axis=1, inplace=True)
        df.rename(
            columns={
                mapping['ss_col_name']: mapping['db_col_name']
                for mapping in self.mappings
            },
            inplace=True
        )
        return df

    def to_sql(self, df):
        """Produce sqlite database from pandas DataFrame.
        Args:
            df (pd.DataFrame): Compiled SmartSheet data
        """
        table = self.name.replace(' ', '_')
        engine = create_engine('sqlite:///{}'.format(self.db_file), echo=False)
        df.to_sql(table, engine, if_exists='replace', index=False)


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
    df = sheet.prep_table()
    sheet.to_sql(df)
