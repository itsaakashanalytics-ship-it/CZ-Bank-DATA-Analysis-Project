# ================================================================
# ONE-TIME EXPORT: SQL Server → CSV files for deployment
#
# Run this LOCALLY (where you can actually reach SQL Server — e.g. your
# machine, using Windows/Trusted auth). It pulls all 8 tables and writes
# them to ./data/ as CSVs using the exact filenames data_prep.py expects,
# so the deployed Streamlit app can just read those files instead of
# needing a live SQL connection (which Streamlit Cloud can't reach anyway).
#
# Large tables (like a multi-year merged transaction table) are
# automatically gzip-compressed if they'd be too big to commit comfortably
# — data_prep.py's loader picks up the .gz version transparently.
#
# Usage:
#   python export_sql_to_csv.py --server "MYSERVER\SQLEXPRESS" --database BankDB
# ================================================================

import argparse
import gzip
import os
import shutil

from data_prep import load_raw_tables_sql, DEFAULT_FILES

# Size (in MB) above which a CSV gets gzip-compressed before committing.
# GitHub's web upload caps out around 25MB per file; git push itself allows
# up to 100MB without Git LFS, but smaller commits push faster and diff better.
GZIP_THRESHOLD_MB = 20


def export(server, database, out_dir='data', schema='dbo', trusted_connection=True,
           username=None, password=None, table_overrides=None):
    os.makedirs(out_dir, exist_ok=True)

    print(f"Connecting to {server}/{database} ...")
    raw = load_raw_tables_sql(
        server=server, database=database, schema=schema,
        trusted_connection=trusted_connection, username=username, password=password,
        tables=table_overrides,
    )
    print("✅ Pulled all 8 tables. Writing CSVs...")

    total_bytes = 0
    for logical_name, df in raw.items():
        filename = DEFAULT_FILES[logical_name]  # e.g. 'trans.csv'
        path = os.path.join(out_dir, filename)
        df.to_csv(path, sep=';', index=False)

        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > GZIP_THRESHOLD_MB:
            gz_path = path + '.gz'
            with open(path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(path)  # keep only the compressed version
            gz_size_mb = os.path.getsize(gz_path) / (1024 * 1024)
            print(f"  {filename:20s} {size_mb:8.1f} MB → gzip'd to {gz_size_mb:6.1f} MB "
                  f"({os.path.basename(gz_path)})")
            total_bytes += os.path.getsize(gz_path)
        else:
            print(f"  {filename:20s} {size_mb:8.1f} MB")
            total_bytes += os.path.getsize(path)

    print(f"\n✅ Done. Total on-disk size: {total_bytes / (1024*1024):.1f} MB in '{out_dir}/'")
    print(f"   Next: git add {out_dir} && git commit -m \"Add exported data\" && git push")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export SQL Server tables to CSV for deployment.")
    parser.add_argument('--server', required=True, help='SQL Server hostname\\instance')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--schema', default='dbo')
    parser.add_argument('--out-dir', default='data')
    parser.add_argument('--username', default=None, help='Omit for Windows/Trusted auth')
    parser.add_argument('--password', default=None, help='Omit for Windows/Trusted auth')
    parser.add_argument('--transaction-table', default=None,
                         help="Override if your transaction table isn't named 'transaction', "
                              "e.g. --transaction-table Transaction_Merged")
    args = parser.parse_args()

    overrides = {}
    if args.transaction_table:
        overrides['transaction'] = args.transaction_table

    export(
        server=args.server, database=args.database, out_dir=args.out_dir, schema=args.schema,
        trusted_connection=(args.username is None), username=args.username, password=args.password,
        table_overrides=overrides or None,
    )
