# ================================================================
# CZECHOSLOVAKIA BANK — DESCRIPTIVE & DIAGNOSTIC ANALYSIS
# Section A: Descriptive EDA   |   Section B: Diagnostic EDA
#
# Run standalone:  python descriptive_analysis.py --data-dir ./data
# ================================================================

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from data_prep import load_raw_tables, prepare_data, NAVY, TEAL, ORANGE, GREEN, RED, GOLD
from chart_utils import add_bar_labels

plt.style.use('seaborn-v0_8-whitegrid')


def run_descriptive_analysis(data, show=True):
    """
    Runs Sections A (A1-A6) and B (B1-B6).
    `data` is the dict returned by data_prep.prepare_data().
    Returns a dict of KPIs so the Streamlit app / predictive script can reuse them.
    """
    account      = data['account']
    client       = data['client']
    district     = data['district']
    disp         = data['disp']
    card         = data['card']
    loan         = data['loan']
    transaction  = data['transaction']
    acc_cli      = data['acc_cli']
    loan_cli     = data['loan_cli']
    acc_district = data['acc_district']

    kpis = {}

    # ================================================================
    # SECTION A — DESCRIPTIVE EDA
    # ================================================================

    # ── A1. CUSTOMER DEMOGRAPHICS ───────────────────────────────────
    print("\n===== A1. CUSTOMER DEMOGRAPHICS =====")
    print(f"Total Clients     : {client['client_id'].nunique():,}")
    print(f"Avg Age           : {client['age'].mean():.1f}")
    print(f"Female %          : {(client['gender']=='F').mean()*100:.1f}%")
    print(f"Districts covered : {client['district_id'].nunique()}")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('A1 — Customer Demographics', fontsize=14, fontweight='bold')

    axes[0].hist(client['age'], bins=25, color=TEAL, edgecolor='white')
    axes[0].axvline(client['age'].mean(), color=ORANGE, lw=2,
                    label=f"Avg={client['age'].mean():.0f}")
    axes[0].set_title('Age Distribution'); axes[0].set_xlabel('Age')
    axes[0].legend()

    g = client['gender'].value_counts()
    axes[1].pie(g, labels=['Male', 'Female'], colors=[NAVY, TEAL],
                autopct='%1.1f%%', startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    axes[1].set_title('Gender Split')

    ag = client.groupby(['age_group', 'gender']).size().unstack(fill_value=0)
    ag.plot(kind='bar', ax=axes[2], color=[NAVY, TEAL], edgecolor='white')
    axes[2].set_title('Age Group by Gender'); axes[2].set_xlabel('')
    axes[2].tick_params(axis='x', rotation=30)
    add_bar_labels(axes[2], fmt='{:,.0f}')
    plt.tight_layout()
    if show: plt.show()

    # ── A2. ACCOUNT ANALYSIS ────────────────────────────────────────
    print("\n===== A2. ACCOUNT ANALYSIS =====")
    print(f"Total Accounts   : {account['account_id'].nunique():,}")
    print(f"Account Types    :\n{account['Account_type'].value_counts()}")
    print(f"Frequency dist   :\n{account['frequency'].value_counts()}")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('A2 — Account Analysis', fontsize=14, fontweight='bold')

    yr = account.groupby('acc_year')['account_id'].count()
    axes[0].plot(yr.index, yr.values, color=TEAL, marker='o', lw=2.5)
    axes[0].fill_between(yr.index, yr.values, alpha=0.15, color=TEAL)
    axes[0].set_title('New Accounts per Year'); axes[0].set_xlabel('Year')
    for x, y in zip(yr.index, yr.values):
        axes[0].annotate(f'{y:,.0f}', (x, y), textcoords='offset points',
                          xytext=(0, 6), ha='center', fontsize=8)

    at = account['Account_type'].value_counts()
    axes[1].bar(at.index, at.values, color=NAVY, edgecolor='white')
    axes[1].set_title('Accounts by Type'); axes[1].set_xlabel('Type')
    axes[1].tick_params(axis='x', rotation=20)
    add_bar_labels(axes[1], fmt='{:,.0f}')

    if 'gender' in acc_cli.columns:
        ag2 = acc_cli.groupby(['Account_type', 'gender']).size().unstack(fill_value=0)
        ag2.plot(kind='bar', ax=axes[2], color=[NAVY, TEAL])
        axes[2].set_title('Account Type by Gender')
        axes[2].tick_params(axis='x', rotation=20)
        add_bar_labels(axes[2], fmt='{:,.0f}')
    plt.tight_layout()
    if show: plt.show()

    # ── A3. TRANSACTION OVERVIEW ─────────────────────────────────────
    print("\n===== A3. TRANSACTION OVERVIEW =====")
    total_txns   = len(transaction)
    total_credit = transaction[transaction['type_lbl'] == 'Credit']['amount'].sum()
    total_debit  = transaction[transaction['type_lbl'] == 'Debit']['amount'].sum()
    avg_txn      = transaction['amount'].mean()

    print(f"Total Transactions  : {total_txns:,}")
    print(f"Total Credit (CZK)  : {total_credit:,.0f}")
    print(f"Total Debit  (CZK)  : {total_debit:,.0f}")
    print(f"Avg Txn Amount      : {avg_txn:,.2f}")
    print(f"Credit:Debit Ratio  : {total_credit/total_debit:.2f}")

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('A3 — Transaction Overview', fontsize=14, fontweight='bold')

    monthly = (transaction.groupby(['year', 'month', 'type_lbl'])['amount']
               .sum().reset_index())
    monthly['period'] = pd.to_datetime(
        monthly['year'].astype(str) + '-' + monthly['month'].astype(str).str.zfill(2))
    for t, c in [('Credit', GREEN), ('Debit', RED)]:
        sub = monthly[monthly['type_lbl'] == t].sort_values('period')
        axes[0, 0].plot(sub['period'], sub['amount'] / 1e6, label=t, color=c, lw=2)
    axes[0, 0].set_title('Monthly Credit vs Debit (M CZK)')
    axes[0, 0].legend(); axes[0, 0].set_xlabel('Month')
    axes[0, 0].xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())
    axes[0, 0].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y'))

    axes[0, 1].hist(np.log1p(transaction['amount']), bins=40, color=NAVY, edgecolor='white')
    axes[0, 1].set_title('Txn Amount Distribution (log scale)')
    axes[0, 1].set_xlabel('log(Amount + 1)')

    op = transaction['operation'].value_counts().head(7)
    axes[1, 0].barh(op.index, op.values, color=TEAL)
    axes[1, 0].set_title('Top Operation Types')
    add_bar_labels(axes[1, 0], fmt='{:,.0f}')

    pu = transaction['Purpose'].value_counts().head(7)
    axes[1, 1].bar(pu.index, pu.values, color=ORANGE)
    axes[1, 1].set_title('Transaction by Purpose')
    axes[1, 1].tick_params(axis='x', rotation=30)
    add_bar_labels(axes[1, 1], fmt='{:,.0f}')
    plt.tight_layout()
    if show: plt.show()

    yearly_txn = transaction.groupby('year').agg(
        count=('trans_id', 'count'),
        credit=('amount', lambda x: x[transaction.loc[x.index, 'type_lbl'] == 'Credit'].sum()),
        debit=('amount', lambda x: x[transaction.loc[x.index, 'type_lbl'] == 'Debit'].sum()),
        avg=('amount', 'mean')
    ).reset_index()
    print("\nYearly Summary:")
    print(yearly_txn.round(0).to_string(index=False))

    # ── A4. LOAN OVERVIEW ───────────────────────────────────────────
    print("\n===== A4. LOAN OVERVIEW =====")
    print(f"Total Loans         : {len(loan):,}")
    print(f"Total Exposure(CZK) : {loan['amount'].sum():,.0f}")
    print(f"Default Rate        : {loan['is_default'].mean()*100:.2f}%")
    print(f"Avg Loan Amount     : {loan['amount'].mean():,.0f}")
    print(f"Avg Duration(months): {loan['duration'].mean():.1f}")
    print(f"\nStatus breakdown:\n{loan['status_lbl'].value_counts()}")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('A4 — Loan Overview', fontsize=14, fontweight='bold')

    sc = loan['status_lbl'].value_counts()
    axes[0].pie(sc, labels=sc.index, colors=[GREEN, GOLD, TEAL, RED],
                autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.55})
    axes[0].set_title('Loan Status Mix')

    colors_s = {'Completed OK': GREEN, 'Completed Issue': GOLD, 'Active': TEAL, 'Default': RED}
    for s, grp in loan.groupby('status_lbl'):
        axes[1].hist(grp['amount'] / 1000, bins=25, alpha=0.55,
                     color=colors_s.get(s, 'gray'), label=s)
    axes[1].set_title('Loan Amount by Status')
    axes[1].set_xlabel('Amount (000s CZK)'); axes[1].legend(fontsize=8)

    ly = loan.groupby('year')['loan_id'].count()
    axes[2].bar(ly.index, ly.values, color=NAVY, edgecolor='white')
    axes[2].set_title('Loans Issued per Year')
    add_bar_labels(axes[2], fmt='{:,.0f}')
    plt.tight_layout()
    if show: plt.show()

    # ── A5. CARD & PRODUCT ADOPTION ─────────────────────────────────
    print("\n===== A5. CARD & PRODUCT ADOPTION =====")
    total_cards = len(card)
    total_accs  = account['account_id'].nunique()
    penetration = total_cards / total_accs * 100
    print(f"Total Cards Issued   : {total_cards:,}")
    print(f"Card Penetration Rate: {penetration:.1f}%")
    print(f"Card Types:\n{card['type'].value_counts()}")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('A5 — Card & Product Adoption', fontsize=14, fontweight='bold')

    ct = card['type'].str.lower().value_counts()
    axes[0].pie(ct, labels=ct.index, colors=[NAVY, GOLD, TEAL],
                autopct='%1.1f%%', startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    axes[0].set_title('Card Types')

    cy = card.groupby('card_year')['card_id'].count()
    axes[1].bar(cy.index, cy.values, color=TEAL, edgecolor='white')
    axes[1].set_title('Cards Issued per Year')
    add_bar_labels(axes[1], fmt='{:,.0f}')

    categories = ['Accounts with Card', 'Accounts without Card']
    values = [total_cards, total_accs - total_cards]
    axes[2].bar(categories, values, color=[GREEN, RED], edgecolor='white')
    axes[2].set_title(f'Card Penetration = {penetration:.1f}%')
    add_bar_labels(axes[2], fmt='{:,.0f}')
    plt.tight_layout()
    if show: plt.show()

    # ── A6. REGIONAL / DISTRICT ANALYSIS ────────────────────────────
    print("\n===== A6. REGIONAL / DISTRICT ANALYSIS =====")
    print("Top 10 Districts:")
    print(acc_district.sort_values('acc_count', ascending=False)
          [['name', 'region', 'acc_count', 'avg_salary']].head(10).to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('A6 — Regional / District Analysis', fontsize=14, fontweight='bold')

    top10 = acc_district.nlargest(10, 'acc_count')
    axes[0].barh(top10['name'], top10['acc_count'], color=NAVY)
    axes[0].set_title('Top 10 Districts by Accounts')
    axes[0].set_xlabel('Number of Accounts')
    add_bar_labels(axes[0], fmt='{:,.0f}')

    axes[1].scatter(acc_district['avg_salary'], acc_district['acc_per_1000'],
                    color=TEAL, alpha=0.7, s=60)
    axes[1].set_title('Avg Salary vs Account Density')
    axes[1].set_xlabel('Average Salary (CZK)')
    axes[1].set_ylabel('Accounts per 1000 People')
    for _, r in acc_district.nlargest(4, 'acc_per_1000').iterrows():
        axes[1].annotate(r['name'], (r['avg_salary'], r['acc_per_1000']),
                          fontsize=7, xytext=(4, 4), textcoords='offset points')
    plt.tight_layout()
    if show: plt.show()

    # ================================================================
    # SECTION B — DIAGNOSTIC EDA
    # ================================================================

    # ── B1. HIGH DEBIT ACCOUNT RATIO ─────────────────────────────────
    print("\n===== B1. WHY DO SOME ACCOUNTS HAVE HIGH DEBIT ACTIVITY? =====")
    txn_by_acc = transaction.groupby(['account_id', 'type_lbl'])['amount'].sum().unstack(fill_value=0)
    if 'Credit' not in txn_by_acc.columns: txn_by_acc['Credit'] = 0
    if 'Debit'  not in txn_by_acc.columns: txn_by_acc['Debit']  = 0
    txn_by_acc['debit_ratio'] = (
        txn_by_acc['Debit'] / (txn_by_acc['Credit'] + txn_by_acc['Debit'] + 1))
    txn_by_acc['is_high_debit'] = (txn_by_acc['debit_ratio'] > 0.7).astype(int)
    txn_by_acc = txn_by_acc.reset_index()

    high_debit_rate = txn_by_acc['is_high_debit'].mean() * 100
    print(f"High-Debit Account Ratio (KPI): {high_debit_rate:.1f}%")
    kpis['high_debit_rate'] = high_debit_rate

    txn_type = txn_by_acc.merge(
        account[['account_id', 'Account_type', 'district_id']], on='account_id', how='left')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('B1 — High Debit Activity Analysis', fontsize=14, fontweight='bold')

    hd_by_type = txn_type.groupby('Account_type')['is_high_debit'].mean() * 100
    axes[0].bar(hd_by_type.index, hd_by_type.values, color=RED, edgecolor='white')
    axes[0].set_title('High-Debit Rate by Account Type (%)')
    axes[0].set_xlabel('Account Type')
    axes[0].tick_params(axis='x', rotation=20)
    add_bar_labels(axes[0], fmt='{:.1f}%')

    axes[1].hist(txn_by_acc['debit_ratio'], bins=30, color=NAVY, edgecolor='white')
    axes[1].axvline(0.7, color=RED, linestyle='--', lw=2, label='High-debit threshold')
    axes[1].set_title('Distribution of Debit Ratio per Account')
    axes[1].set_xlabel('Debit / Total Ratio')
    axes[1].legend()
    plt.tight_layout()
    if show: plt.show()

    # ── B2. LOAN DEFAULT FACTORS ─────────────────────────────────────
    print("\n===== B2. WHAT FACTORS INFLUENCE LOAN DEFAULT? =====")
    default_rate = loan_cli['is_default'].mean() * 100
    print(f"Overall Default Rate (KPI): {default_rate:.2f}%")
    kpis['default_rate'] = default_rate

    defaulters     = loan_cli[loan_cli['is_default'] == 1]
    non_defaulters = loan_cli[loan_cli['is_default'] == 0]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('B2 — Loan Default Factor Analysis', fontsize=14, fontweight='bold')

    axes[0, 0].hist(non_defaulters['age'].dropna(), bins=20, alpha=0.6,
                    color=GREEN, label='No Default', density=True)
    axes[0, 0].hist(defaulters['age'].dropna(), bins=20, alpha=0.6,
                    color=RED, label='Default', density=True)
    axes[0, 0].set_title('Age: Default vs No Default')
    axes[0, 0].legend()

    axes[0, 1].boxplot(
        [non_defaulters['amount'].dropna() / 1000, defaulters['amount'].dropna() / 1000],
        labels=['No Default', 'Default'], patch_artist=True,
        boxprops=dict(facecolor='#EFF6FF'), medianprops=dict(color=NAVY, linewidth=2))
    axes[0, 1].set_title('Loan Amount (000s CZK): Default vs No Default')

    if 'avg_salary' in loan_cli.columns:
        sal_df = loan_cli.dropna(subset=['avg_salary', 'is_default'])
        sal_bins = pd.qcut(sal_df['avg_salary'], q=5, duplicates='drop')
        dr_sal = sal_df.groupby(sal_bins)['is_default'].mean() * 100
        axes[1, 0].bar(range(len(dr_sal)), dr_sal.values, color=ORANGE)
        axes[1, 0].set_title('Default Rate by District Salary Quintile')
        axes[1, 0].set_xlabel('Salary Quintile (Q1=Lowest)')
        axes[1, 0].set_ylabel('Default Rate (%)')
        axes[1, 0].set_xticks(range(len(dr_sal)))
        axes[1, 0].set_xticklabels([f'Q{i+1}' for i in range(len(dr_sal))])
        add_bar_labels(axes[1, 0], fmt='{:.1f}%')

    if 'gender' in loan_cli.columns:
        dr_gen = loan_cli.groupby('gender')['is_default'].mean() * 100
        axes[1, 1].bar(dr_gen.index, dr_gen.values, color=[NAVY, TEAL])
        axes[1, 1].set_title('Default Rate by Gender')
        axes[1, 1].set_xlabel('Gender')
        axes[1, 1].set_ylabel('Default Rate (%)')
        add_bar_labels(axes[1, 1], fmt='{:.1f}%')

    plt.tight_layout()
    if show: plt.show()

    compare = loan_cli.groupby('is_default')[
        [c for c in ['age', 'amount', 'duration', 'avg_salary'] if c in loan_cli.columns]
    ].mean()
    compare.index = ['No Default', 'Default']
    print("\nDefaulter vs Non-Defaulter Averages:")
    print(compare.round(1).T.to_string())

    # ── B3. DISTRICT ACCOUNT PENETRATION ─────────────────────────────
    print("\n===== B3. WHY ARE SOME DISTRICTS LOW IN ACCOUNT OPENING? =====")
    pen_df = acc_district.copy()
    pen_df['acc_per_1000'] = pen_df['acc_count'] / pen_df['population'] * 1000
    avg_pen = pen_df['acc_per_1000'].mean()
    print(f"Avg Account Penetration (KPI): {avg_pen:.2f} per 1000 people")
    kpis['avg_penetration'] = avg_pen

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('B3 — District Account Penetration', fontsize=14, fontweight='bold')

    axes[0].scatter(pen_df['avg_salary'], pen_df['acc_per_1000'], color=TEAL, alpha=0.7, s=60)
    axes[0].set_title('Account Penetration vs Avg Salary')
    axes[0].set_xlabel('Avg Salary (CZK)')
    axes[0].set_ylabel('Accounts per 1000 People')
    m, b = np.polyfit(pen_df['avg_salary'].dropna(), pen_df['acc_per_1000'].dropna(), 1)
    x_line = np.linspace(pen_df['avg_salary'].min(), pen_df['avg_salary'].max(), 100)
    axes[0].plot(x_line, m * x_line + b, color=ORANGE, lw=2, linestyle='--', label='Trend')
    axes[0].legend()

    axes[1].scatter(pen_df['unemp_96'], pen_df['acc_per_1000'], color=RED, alpha=0.7, s=60)
    axes[1].set_title('Account Penetration vs Unemployment Rate')
    axes[1].set_xlabel('Unemployment Rate 1996 (%)')
    axes[1].set_ylabel('Accounts per 1000 People')
    plt.tight_layout()
    if show: plt.show()

    print("\nLowest Penetration Districts:")
    print(pen_df.nsmallest(10, 'acc_per_1000')[
        ['name', 'region', 'population', 'acc_count', 'acc_per_1000', 'avg_salary', 'unemp_96']
    ].round(2).to_string(index=False))

    # ── B4. CARD ADOPTION DRIVERS ────────────────────────────────────
    print("\n===== B4. WHAT DRIVES CARD ADOPTION? =====")
    card_adop_rate = acc_cli['has_card'].mean() * 100
    print(f"Card Adoption Rate (KPI): {card_adop_rate:.1f}%")
    kpis['card_adoption_rate'] = card_adop_rate

    txn_acc = transaction.groupby('account_id').agg(
        txn_count=('trans_id', 'count'),
        avg_txn=('amount', 'mean'),
        avg_bal=('balance', 'mean')).reset_index()
    acc_cli2 = acc_cli.merge(txn_acc, on='account_id', how='left')

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('B4 — Card Adoption Drivers', fontsize=14, fontweight='bold')

    card_groups = {0: 'No Card', 1: 'Has Card'}
    for gval, lbl in card_groups.items():
        sub = acc_cli2[acc_cli2['has_card'] == gval]['avg_txn'].dropna()
        axes[0].hist(sub, bins=25, alpha=0.6, color=(TEAL if gval == 1 else RED),
                     label=lbl, density=True)
    axes[0].set_title('Avg Txn Amount: Card vs No Card')
    axes[0].legend()

    for gval, lbl in card_groups.items():
        sub = acc_cli2[acc_cli2['has_card'] == gval]['age'].dropna()
        axes[1].hist(sub, bins=20, alpha=0.6, color=(TEAL if gval == 1 else RED),
                     label=lbl, density=True)
    axes[1].set_title('Age: Card vs No Card')
    axes[1].legend()

    car_by_type = acc_cli2.groupby('Account_type')['has_card'].mean() * 100
    axes[2].bar(car_by_type.index, car_by_type.values, color=NAVY, edgecolor='white')
    axes[2].set_title('Card Adoption Rate by Account Type (%)')
    axes[2].tick_params(axis='x', rotation=20)
    add_bar_labels(axes[2], fmt='{:.1f}%')
    plt.tight_layout()
    if show: plt.show()

    print("\nCard vs No-Card Avg Comparison:")
    print(acc_cli2.groupby('has_card')[
        [c for c in ['age', 'avg_txn', 'avg_bal', 'txn_count'] if c in acc_cli2.columns]
    ].mean().round(1))

    # ── B5. DORMANT ACCOUNTS ─────────────────────────────────────────
    print("\n===== B5. WHY DO SOME ACCOUNTS HAVE NO TRANSACTIONS? =====")
    active_accs  = set(transaction['account_id'].unique())
    all_accs     = set(account['account_id'].unique())
    dormant_ids  = all_accs - active_accs
    dormant_rate = len(dormant_ids) / len(all_accs) * 100
    print(f"Dormant Account Rate (KPI): {dormant_rate:.1f}%")
    print(f"Active : {len(active_accs):,}  |  Dormant : {len(dormant_ids):,}")
    kpis['dormant_rate'] = dormant_rate

    account['is_dormant'] = account['account_id'].isin(dormant_ids).astype(int)
    dormant_df = account.merge(
        district[['district_id', 'name', 'region', 'avg_salary']], on='district_id', how='left')

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('B5 — Dormant Account Analysis', fontsize=14, fontweight='bold')

    dorm_type = dormant_df.groupby('Account_type')['is_dormant'].mean() * 100
    axes[0].bar(dorm_type.index, dorm_type.values, color=ORANGE, edgecolor='white')
    axes[0].set_title('Dormant Rate by Account Type (%)')
    axes[0].tick_params(axis='x', rotation=20)
    add_bar_labels(axes[0], fmt='{:.1f}%')

    dorm_region = dormant_df.groupby('region')['is_dormant'].mean() * 100
    axes[1].barh(dorm_region.index, dorm_region.values, color=NAVY)
    axes[1].set_title('Dormant Rate by Region (%)')
    add_bar_labels(axes[1], fmt='{:.1f}%')
    plt.tight_layout()
    if show: plt.show()

    # ── B6. DECLINING TRANSACTION TYPES ─────────────────────────────
    print("\n===== B6. WHICH TRANSACTION TYPES ARE DECLINING? =====")
    txn_trend = (transaction.groupby(['year', 'type_lbl'])['amount'].sum().reset_index())
    print("\nTransaction volume by year & type:")
    print(txn_trend.pivot(index='year', columns='type_lbl', values='amount').round(0).to_string())

    op_trend = (transaction.groupby(['year', 'operation'])['trans_id']
                .count().reset_index(name='count'))

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    fig.suptitle('B6 — Transaction Type Trends', fontsize=14, fontweight='bold')

    for t, c in [('Credit', GREEN), ('Debit', RED)]:
        sub = txn_trend[txn_trend['type_lbl'] == t]
        axes[0].plot(sub['year'], sub['amount'] / 1e6, label=t, color=c, marker='o', lw=2.5)
    axes[0].set_title('Credit vs Debit Volume by Year (M CZK)')
    axes[0].legend(); axes[0].set_xlabel('Year')

    op_pivot = op_trend.pivot(index='operation', columns='year', values='count').fillna(0)
    if op_pivot.empty or op_pivot.shape[0] == 0 or op_pivot.shape[1] == 0:
        axes[1].text(0.5, 0.5,
                      "No data to plot here.\n(operation/year came back empty —\n"
                      "check that 'operation' and the date column\n"
                      "in your transaction table are populated.)",
                      ha='center', va='center', fontsize=9, color=RED, wrap=True)
        axes[1].set_title('Transaction Count by Operation Type & Year — no data')
        axes[1].axis('off')
        print("⚠️  B6 heatmap skipped: 'operation'/'year' groupby returned no rows. "
              "Check transaction date parsing and the 'operation' column.")
    else:
        sns.heatmap(op_pivot, ax=axes[1], cmap='Blues', annot=True, fmt='.0f',
                    linewidths=0.5, annot_kws={'size': 8})
        axes[1].set_title('Transaction Count by Operation Type & Year')
        axes[1].set_xlabel('Year'); axes[1].set_ylabel('Operation')
    plt.tight_layout()
    if show: plt.show()

    # ── KPIs carried forward for the FINAL SUMMARY / Streamlit app ──
    kpis['total_clients']   = client['client_id'].nunique()
    kpis['avg_age']         = client['age'].mean()
    kpis['female_pct']      = (client['gender'] == 'F').mean() * 100
    kpis['total_accounts']  = account['account_id'].nunique()
    kpis['total_txns']      = len(transaction)
    kpis['total_credit']    = total_credit
    kpis['total_debit']     = total_debit
    kpis['total_loans']     = len(loan)
    kpis['total_exposure']  = loan['amount'].sum()
    kpis['card_penetration'] = penetration

    return kpis


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run descriptive & diagnostic bank EDA.')
    parser.add_argument('--data-dir', default='.', help='Folder containing the raw CSV files')
    args = parser.parse_args()

    raw = load_raw_tables(args.data_dir)
    data = prepare_data(**raw)
    run_descriptive_analysis(data, show=True)
