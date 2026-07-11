# ================================================================
# CZECHOSLOVAKIA BANK — MAIN ORCHESTRATOR
# Runs descriptive_analysis.py then predictive_analysis.py back-to-back
# and prints the combined FINAL KPI SUMMARY (same as the original
# single-file script), using data_prep.py as the single source of truth
# for data loading so nothing is computed twice.
#
# Usage:  python main.py --data-dir ./data --model-dir ./model
# ================================================================

import argparse

from data_prep import load_raw_tables, load_raw_tables_sql, prepare_data
from descriptive_analysis import run_descriptive_analysis
from predictive_analysis import run_predictive_analysis


def main(data_dir='.', model_dir='model', show=True,
         source='csv', sql_server=None, sql_database=None, sql_schema='dbo',
         trusted_connection=True, sql_username=None, sql_password=None):
    print("Loading & preparing data...")
    if source == 'sql':
        raw = load_raw_tables_sql(
            server=sql_server, database=sql_database, schema=sql_schema,
            trusted_connection=trusted_connection,
            username=sql_username, password=sql_password,
        )
    else:
        raw = load_raw_tables(data_dir)
    data = prepare_data(**raw)
    print("✅ Data prep done. Ready for analysis.")

    desc_kpis = run_descriptive_analysis(data, show=show)
    pred_results = run_predictive_analysis(data, model_dir=model_dir, show=show)

    print("\n" + "=" * 55)
    print("  FINAL KPI SUMMARY — USE IN POWERBI & PRESENTATION")
    print("=" * 55)
    print(f"  Total Clients              : {desc_kpis['total_clients']:,}")
    print(f"  Avg Client Age             : {desc_kpis['avg_age']:.1f} yrs")
    print(f"  Female %                   : {desc_kpis['female_pct']:.1f}%")
    print(f"  Total Accounts             : {desc_kpis['total_accounts']:,}")
    print(f"  Total Transactions         : {desc_kpis['total_txns']:,}")
    print(f"  Total Credit Volume (CZK)  : {desc_kpis['total_credit']:,.0f}")
    print(f"  Total Debit Volume  (CZK)  : {desc_kpis['total_debit']:,.0f}")
    print(f"  Total Loans                : {desc_kpis['total_loans']:,}")
    print(f"  Total Loan Exposure (CZK)  : {desc_kpis['total_exposure']:,.0f}")
    print(f"  Loan Default Rate          : {desc_kpis['default_rate']:.2f}%")
    print(f"  Card Penetration Rate      : {desc_kpis['card_penetration']:.1f}%")
    print(f"  Dormant Account Rate       : {desc_kpis['dormant_rate']:.1f}%")
    print(f"  High-Debit Account Ratio   : {desc_kpis['high_debit_rate']:.1f}%")
    print(f"  Loan Default Model AUC     : {pred_results['c1']['auc']:.4f}")
    print(f"  Txn Forecast R²            : {pred_results['c2']['r2']:.4f}")
    print("=" * 55)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the full bank analysis pipeline.')
    parser.add_argument('--data-dir', default='.', help='Folder containing the raw CSV files (source=csv)')
    parser.add_argument('--model-dir', default='model', help='Folder to save trained models into')
    parser.add_argument('--source', default='csv', choices=['csv', 'sql'],
                         help='Where to load the 8 raw tables from')
    parser.add_argument('--sql-server', default=None, help='SQL Server hostname\\instance')
    parser.add_argument('--sql-database', default=None, help='SQL Server database name')
    parser.add_argument('--sql-schema', default='dbo', help='Schema for the tables (default: dbo)')
    parser.add_argument('--sql-username', default=None, help='SQL login username (omit for Windows auth)')
    parser.add_argument('--sql-password', default=None, help='SQL login password (omit for Windows auth)')
    args = parser.parse_args()

    main(data_dir=args.data_dir, model_dir=args.model_dir, source=args.source,
         sql_server=args.sql_server, sql_database=args.sql_database, sql_schema=args.sql_schema,
         trusted_connection=(args.sql_username is None), sql_username=args.sql_username,
         sql_password=args.sql_password)
