# ================================================================
# CZECHOSLOVAKIA BANK — SHARED DATA PREP MODULE
# Loads raw CSVs, cleans them, engineers features, and builds the
# joined tables used by both descriptive_analysis.py,
# predictive_analysis.py, and streamlit_app.py.
#
# EDIT THE FILE PATHS / SEPARATOR BELOW TO MATCH YOUR DATA FOLDER.
# ================================================================

import pandas as pd
import numpy as np

# ── COLOR PALETTE (shared across all scripts) ───────────────────
NAVY   = '#1B3A6B'
TEAL   = '#028090'
ORANGE = '#F97316'
GREEN  = '#059669'
RED    = '#DC2626'
GOLD   = '#D97706'

# ── DEFAULT FILE NAMES ───────────────────────────────────────────
# Classic "Berka" Czech bank dataset file names. Adjust if yours differ.
DEFAULT_FILES = {
    'account':     'account.csv',
    'client':      'client.csv',
    'district':    'district.csv',
    'disp':        'disp.csv',
    'card':        'card.csv',
    'loan':        'loan.csv',
    'orders':      'order.csv',
    'transaction': 'trans.csv',
}


def _read_csv(data_dir, filename, sep=';'):
    import os
    path = f"{data_dir.rstrip('/')}/{filename}"
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        path = path + '.gz'  # transparently use a gzip-compressed export if present
    try:
        return pd.read_csv(path, sep=sep, low_memory=False)
    except Exception:
        # Fall back to comma-separated if semicolon parse fails
        return pd.read_csv(path, low_memory=False)


def load_raw_tables(data_dir='.', files=None, sep=';'):
    """Reads all 8 raw CSVs from data_dir and returns them as a dict of DataFrames."""
    files = files or DEFAULT_FILES
    return {name: _read_csv(data_dir, fname, sep=sep) for name, fname in files.items()}


# ── DEFAULT SQL SERVER TABLE NAMES ───────────────────────────────
# Logical name -> actual table name in your database. Adjust to match
# your schema (e.g. 'dbo.account', 'bank.dbo.transaction', etc).
DEFAULT_TABLES = {
    'account':     'account',
    'client':      'client',
    'district':    'district',
    'disp':        'disp',
    'card':        'card',
    'loan':        'loan',
    'orders':      'order',
    'transaction': 'transaction',
}


def build_sql_connection_string(server, database, driver='ODBC Driver 17 for SQL Server',
                                 trusted_connection=True, username=None, password=None,
                                 dialect='pyodbc', port=1433):
    """
    Builds a SQLAlchemy connection string for SQL Server.

    dialect='pyodbc' (default): needs the Microsoft ODBC driver installed on
        the host machine. Supports Windows/Trusted auth. Best for local runs
        or Windows-based deployment targets.
    dialect='pymssql': pure-Python driver, nothing to install on the host —
        works out-of-the-box on Streamlit Community Cloud. Does NOT support
        Windows/Trusted auth; requires a SQL Server login (username/password).
    """
    if dialect == 'pymssql':
        if not username or not password:
            raise ValueError("pymssql requires a SQL Server username and password "
                              "(Windows/Trusted auth isn't supported by pymssql).")
        return f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}"

    driver_enc = driver.replace(' ', '+')
    if trusted_connection:
        return (f"mssql+pyodbc://@{server}/{database}"
                f"?driver={driver_enc}&trusted_connection=yes")
    return (f"mssql+pyodbc://{username}:{password}@{server}/{database}"
            f"?driver={driver_enc}")


def load_raw_tables_sql(server=None, database=None, tables=None,
                         driver='ODBC Driver 17 for SQL Server',
                         trusted_connection=True, username=None, password=None,
                         connection_string=None, schema=None, dialect='pyodbc', port=1433):
    """
    Reads all 8 raw tables from SQL Server and returns them as a dict of
    DataFrames — a drop-in replacement for load_raw_tables() when your data
    lives in SQL Server instead of CSVs (e.g. your 6 years of transactions
    already merged into one `transaction` table).

    Pass either:
      - server + database (+ trusted_connection=True for Windows auth, or
        username/password for SQL auth), or
      - a ready-made `connection_string`.

    Set dialect='pymssql' for cloud deployments (e.g. Streamlit Community
    Cloud) where you can't install the Microsoft ODBC driver — pymssql needs
    a SQL login (username/password), not Windows/Trusted auth.

    `tables` lets you override individual table names, e.g. if your
    transaction table is actually called 'Transaction_Merged':
        tables={'transaction': 'Transaction_Merged'}
    Any table not overridden falls back to DEFAULT_TABLES.
    """
    import sqlalchemy as sa

    if connection_string is None:
        if not server or not database:
            raise ValueError("Provide either connection_string, or both server and database.")
        connection_string = build_sql_connection_string(
            server, database, driver=driver, trusted_connection=trusted_connection,
            username=username, password=password, dialect=dialect, port=port)

    engine = sa.create_engine(connection_string)

    table_map = dict(DEFAULT_TABLES)
    if tables:
        table_map.update(tables)

    def _bracket_qualify(schema_part, table_part):
        """Wraps each dot-separated identifier segment in [brackets] so that
        reserved words (e.g. 'order') and special characters don't break the
        query on SQL Server."""
        segments = []
        if schema_part:
            segments.extend(schema_part.split('.'))
        segments.extend(table_part.split('.'))
        return '.'.join(f'[{seg}]' for seg in segments if seg)

    result = {}
    with engine.connect() as conn:
        for logical_name, table_name in table_map.items():
            full_name = _bracket_qualify(schema, table_name)
            result[logical_name] = pd.read_sql(sa.text(f"SELECT * FROM {full_name}"), conn)
    return result


def prepare_data(account, client, district, disp, card, loan, orders, transaction):
    """
    Runs all cleaning / feature engineering / joins on the 8 raw tables.
    Returns a dict containing every derived table & KPI needed downstream,
    so the rest of the pipeline never has to repeat this work.
    """
    account = account.copy()
    client = client.copy()
    district = district.copy()
    disp = disp.copy()
    card = card.copy()
    loan = loan.copy()
    transaction = transaction.copy()

    # ── Decode birth_number & clean dates ────────────────────────
    client['birth_number'] = client['birth_number'].astype(str).str.zfill(6)
    client['month_raw']    = client['birth_number'].str[2:4].astype(int)
    client['gender']       = client['month_raw'].apply(lambda m: 'F' if m > 50 else 'M')
    client['birth_month']  = client['month_raw'].apply(lambda m: m - 50 if m > 50 else m)
    client['birth_year']   = client['birth_number'].str[:2].astype(int) + 1900
    client['age']          = 1998 - client['birth_year']
    client['age_group']    = pd.cut(client['age'],
                                     bins=[0, 25, 35, 45, 55, 65, 100],
                                     labels=['<25', '25-35', '35-45', '45-55', '55-65', '65+'])

    def _parse_bank_date(series):
        """
        Handles both:
          - the legacy Berka CSV encoding, where dates are 6-digit YYMMDD
            integers/strings (e.g. 960130 = 1996-01-30), and
          - native SQL date/datetime columns (e.g. after loading from SQL
            Server), which pandas already reads back as real date objects
            or ISO-formatted strings.
        The old code always assumed the YYMMDD format and, because
        errors='coerce' swallows mismatches instead of raising, silently
        turned every value into NaT when fed a real date/datetime column.
        """
        if pd.api.types.is_datetime64_any_dtype(series):
            return pd.to_datetime(series, errors='coerce')

        # Try a generic parse first — handles ISO strings ('1996-01-30'),
        # datetime.date objects, etc. that come back from SQL Server.
        generic = pd.to_datetime(series, errors='coerce')
        if generic.notna().mean() > 0.5:
            return generic

        # Fall back to the legacy YYMMDD-encoded format from the raw CSVs.
        legacy = pd.to_datetime(series.astype(str).str.zfill(6),
                                 format='%y%m%d', errors='coerce')
        return legacy

    for df, col in [(loan, 'date'), (account, 'date'), (transaction, 'Date')]:
        if col in df.columns:
            df[col] = _parse_bank_date(df[col])

    # ── Sanity check: catch silent date-parsing failures early ───
    for df_name, df, col in [('loan', loan, 'date'), ('account', account, 'date'),
                              ('transaction', transaction, 'Date')]:
        if col in df.columns and df[col].notna().sum() == 0 and len(df) > 0:
            print(f"⚠️  WARNING: every value in {df_name}['{col}'] failed to parse as a date "
                  f"(all became NaT). Check the actual column name/format in your "
                  f"'{df_name}' table — downstream year/month groupbys will come back empty.")

    transaction['year']     = transaction['Date'].dt.year
    transaction['month']    = transaction['Date'].dt.month
    transaction['type_lbl'] = transaction['Type'].map({'PRIJEM': 'Credit', 'VYDAJ': 'Debit'})

    if transaction['type_lbl'].notna().sum() == 0 and len(transaction) > 0:
        print("⚠️  WARNING: transaction['type_lbl'] is entirely empty — the 'Type' column "
              "in your transaction table doesn't contain the expected values "
              "('PRIJEM'/'VYDAJ'). Check the actual values/column name.")

    loan['year']       = loan['date'].dt.year
    loan['is_default'] = (loan['status'] == 'D').astype(int)
    status_map = {'A': 'Completed OK', 'B': 'Completed Issue', 'C': 'Active', 'D': 'Default'}
    loan['status_lbl'] = loan['status'].map(status_map)

    district.rename(columns={'A1': 'district_id', 'A2': 'name', 'A3': 'region',
                              'A4': 'population', 'A11': 'avg_salary',
                              'A12': 'unemp_95', 'A13': 'unemp_96',
                              'A15': 'crimes_95', 'A16': 'crimes_96'}, inplace=True)
    for c in ['population', 'avg_salary', 'unemp_96']:
        if c in district.columns:
            district[c] = pd.to_numeric(district[c], errors='coerce')

    account['acc_year'] = account['date'].dt.year

    date_col = 'issued_date' if 'issued_date' in card.columns else 'issued'
    if date_col in card.columns:
        card['card_year'] = _parse_bank_date(card[date_col]).dt.year

    # ── Master joins (OWNER disposition only) ────────────────────
    owners = disp[disp['type'].str.upper() == 'OWNER'][['account_id', 'client_id']]

    acc_cli = (account
        .merge(owners, on='account_id', how='left')
        .merge(client[['client_id', 'gender', 'age', 'age_group']], on='client_id', how='left')
        .merge(district[['district_id', 'name', 'region', 'population',
                          'avg_salary', 'unemp_96']], on='district_id', how='left'))

    loan_cli = (loan
        .merge(owners, on='account_id', how='left')
        .merge(client[['client_id', 'gender', 'age', 'age_group']], on='client_id', how='left')
        .merge(account[['account_id', 'district_id']], on='account_id', how='left')
        .merge(district[['district_id', 'name', 'avg_salary', 'unemp_96']],
               on='district_id', how='left'))

    # ── Card-holder flag (used by several sections) ──────────────
    card_holders = set(disp.merge(card, on='disp_id')['account_id'])
    acc_cli['has_card'] = acc_cli['account_id'].isin(card_holders).astype(int)

    # ── District-level rollup ─────────────────────────────────────
    acc_district = (account.groupby('district_id')['account_id']
                    .count().reset_index(name='acc_count')
                    .merge(district[['district_id', 'name', 'region',
                                      'population', 'avg_salary', 'unemp_96']],
                           on='district_id', how='left'))
    acc_district['acc_per_1000'] = (
        acc_district['acc_count'] / acc_district['population'] * 1000)

    # ── Feature tables shared by descriptive diagnostics & ML ────
    txn_feat = transaction.groupby('account_id').agg(
        txn_count=('trans_id', 'count'),
        avg_txn_amount=('amount', 'mean'),
        avg_balance=('balance', 'mean'),
        total_credit=('amount', lambda x: x[transaction.loc[x.index, 'type_lbl'] == 'Credit'].sum()),
        total_debit=('amount', lambda x: x[transaction.loc[x.index, 'type_lbl'] == 'Debit'].sum()),
    ).reset_index()

    card_flag = (disp.merge(card[['disp_id']], on='disp_id', how='inner')
                 .groupby('account_id').size().reset_index(name='card_count'))
    card_flag['has_card'] = 1

    return {
        'account': account, 'client': client, 'district': district,
        'disp': disp, 'card': card, 'loan': loan, 'orders': orders,
        'transaction': transaction,
        'acc_cli': acc_cli, 'loan_cli': loan_cli,
        'acc_district': acc_district,
        'txn_feat': txn_feat, 'card_flag': card_flag,
    }


def build_ml_base(loan_cli, txn_feat, card_flag):
    """Builds the shared feature table used by all three ML models in predictive_analysis.py"""
    ml_base = (loan_cli
        .merge(txn_feat, on='account_id', how='left')
        .merge(card_flag[['account_id', 'has_card']], on='account_id', how='left'))
    ml_base['has_card']  = ml_base['has_card'].fillna(0)
    ml_base['is_female'] = (ml_base['gender'] == 'F').astype(int) if 'gender' in ml_base.columns else 0
    for c in ['age', 'avg_salary', 'avg_txn_amount', 'avg_balance', 'txn_count']:
        if c in ml_base.columns:
            ml_base[c] = ml_base[c].fillna(ml_base[c].median())
    return ml_base
