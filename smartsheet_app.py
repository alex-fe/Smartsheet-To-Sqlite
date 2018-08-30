import argparse
import operator
import os
import re
import smartsheet
import sqlite3
import yaml


COLUMN_TYPES = {
    'ABSTRACT_DATETIME': 'NUMERIC',
    'CHECKBOX': 'INTEGER',
    'CONTACT_LIST': 'TEXT',
    'DATE': 'NUMERIC',
    'DURATION': 'TEXT',
    'PICKLIST': 'TEXT',
    'PREDECESSOR': 'TEXT',
    'TEXT_NUMBER': 'TEXT'
}


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
    config['mappings'].sort(key=operator.itemgetter('ss_col_name'))
    return config


def pull_smartsheet(config):
    """Find and parse specified sheet via smartsheet api.
    Args:
        config (dict): Parsed .yml file.
    Returns:
        Sheet object based on name given in .yml attribute 'sheet_name'.
    """
    ss_client = smartsheet.Smartsheet(config['access_token'])
    ss_client.errors_as_exceptions(True)
    sheets = ss_client.Sheets.list_sheets(include_all=True).data
    # TODO: update so if more than one sheet is selected do something
    try:
        sheet_id = next(
            sheet.id for sheet in sheets if sheet.name == config['sheet_name']
        )
    except StopIteration:
        raise SystemExit('Sheet {} was not found'.format(config['sheet_name']))
    else:
        return ss_client.Sheets.get_sheet(sheet_id)


def filter_cols(columns, mappings):
    """Filter the needed columns from the total sheet's columns.
    Args:
        columns (list): The sheets total list of columns.
        mappings(list): The mappings gleaned from config.yml
    Returns:
        Filtered list of columns
    """
    return (
        col for col in columns
        if col.title in [mp['ss_col_name'] for mp in mappings]
    )


def create_sql_command(sheet, config):
    """Create sqlite command with table name and columns.
    Args:
        sheet (Sheet): Sheet object based on name given in .yml attribute
            'sheet_name'.
        config (dict): Parsed .yml file.
    Returns:
            String formatted message to create desired table.
    """
    sql_columns = []
    columns = filter_cols(sheet.columns, config['mappings'])
    for m, col in zip(config['mappings'], columns):
        col = '{} {}'.format(m['db_col_name'], COLUMN_TYPES[col.type])
        sql_columns.append(col)
    table = sheet.name.replace(' ', '_')
    columns = ', '.join(sql_columns)
    return 'CREATE TABLE {} ({})'.format(table, columns)


def to_sql(sheet, config):
    """Produce sqlite database from smartsheet columns.
    Args:
        sheet (Sheet): Sheet object based on name given in .yml attribute
            'sheet_name'.
        config (dict): Parsed .yml file.
    """
    conn = sqlite3.connect(config['db_file'])
    conn = conn.cursor()
    conn.execute(create_sql_command(sheet, config))
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
    config = process_yml(args.config)
    # sheet = pull_smartsheet(config)
    # to_sql(sheet, config)
    from pprint import pprint
    pprint(config)
