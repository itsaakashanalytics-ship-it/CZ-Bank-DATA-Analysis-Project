# ================================================================
# CZECHOSLOVAKIA BANK — PREDICTIVE ANALYSIS
# Section C: Predictive Modelling
#   C1. Loan Default Prediction   (Logistic Regression)
#   C2. Transaction Forecasting   (Linear Regression)
#
# Run standalone:  python predictive_analysis.py --data-dir ./data
# ================================================================

import argparse
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model    import LogisticRegression, LinearRegression
from sklearn.preprocessing   import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, roc_auc_score, classification_report,
                              confusion_matrix, ConfusionMatrixDisplay,
                              mean_absolute_error, r2_score, RocCurveDisplay)

from data_prep import load_raw_tables, prepare_data, build_ml_base, NAVY, TEAL, ORANGE, GREEN, RED
from chart_utils import add_bar_labels

try:
    plt.style.use('seaborn-v0_8-whitegrid')
except (OSError, ValueError):
    plt.style.use('default')


def _require_rows(df_or_X, label, hint):
    """Raises a clear, actionable error instead of letting sklearn fail with a
    cryptic 'n_samples=0' message when upstream data prep produced 0 rows."""
    if len(df_or_X) == 0:
        raise RuntimeError(
            f"\n\n❌ {label} has 0 rows going into model training.\n"
            f"   This means an upstream groupby/merge/date-parse produced no data.\n"
            f"   Likely cause: {hint}\n"
            f"   Check the ⚠️ WARNING lines printed during data loading (data_prep.py) "
            f"for the specific column/table that failed to parse.\n"
        )


def run_predictive_analysis(data, model_dir='model', show=True):
    """
    Runs Section C (C1-C2): trains, evaluates, plots, and pickles both models.
    `data` is the dict returned by data_prep.prepare_data().
    Returns a dict of model metrics/objects for reuse (e.g. by the Streamlit app).
    """
    os.makedirs(model_dir, exist_ok=True)

    transaction = data['transaction']
    disp        = data['disp']
    card        = data['card']
    account     = data['account']
    district    = data['district']
    loan_cli    = data['loan_cli']
    acc_cli     = data['acc_cli']
    txn_feat    = data['txn_feat']
    card_flag   = data['card_flag']

    ml_base = build_ml_base(loan_cli, txn_feat, card_flag)
    results = {}

    # ── C1. LOAN DEFAULT PREDICTION (Logistic Regression) ────────────
    print("\n===== C1. LOAN DEFAULT PREDICTION =====")
    print("Business Value: Reduce credit risk")

    C1 = ml_base[ml_base['status'].isin(['A', 'D'])].copy()
    C1 = C1.dropna(subset=['amount', 'duration', 'payments', 'is_default'])

    FEAT_C1 = [f for f in ['amount', 'duration', 'payments', 'age', 'is_female',
                           'avg_salary', 'has_card', 'avg_txn_amount',
                           'avg_balance', 'txn_count'] if f in C1.columns]
    X1 = C1[FEAT_C1]
    y1 = C1['is_default']

    print(f"Dataset: {len(X1)} rows  |  Features: {FEAT_C1}")
    _require_rows(X1, "C1 loan default dataset",
                  "loan/client/district joins produced no matching rows, or 'status', "
                  "'amount', 'duration', or 'payments' are missing/empty in your loan table.")
    print(f"Class balance: Default={y1.mean()*100:.1f}%  No-Default={100-y1.mean()*100:.1f}%")

    X1_tr, X1_te, y1_tr, y1_te = train_test_split(X1, y1, test_size=0.2,
                                                   random_state=42, stratify=y1)
    sc1 = StandardScaler()
    X1_tr_s = sc1.fit_transform(X1_tr)
    X1_te_s = sc1.transform(X1_te)

    m1 = LogisticRegression(class_weight='balanced', max_iter=500, random_state=42)
    m1.fit(X1_tr_s, y1_tr)

    y1_pred = m1.predict(X1_te_s)
    y1_prob = m1.predict_proba(X1_te_s)[:, 1]
    acc1 = accuracy_score(y1_te, y1_pred)
    auc1 = roc_auc_score(y1_te, y1_prob)

    print(f"\n✅ Accuracy : {acc1*100:.2f}%")
    print(f"✅ AUC-ROC  : {auc1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y1_te, y1_pred, target_names=['No Default', 'Default']))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    fig.suptitle(f'C1 — Loan Default Prediction  |  Accuracy={acc1*100:.1f}%  AUC={auc1:.3f}',
                 fontsize=13, fontweight='bold')

    ConfusionMatrixDisplay(confusion_matrix(y1_te, y1_pred),
        display_labels=['No Default', 'Default']).plot(ax=axes[0], cmap='Blues')
    axes[0].set_title('Confusion Matrix')

    roc1 = RocCurveDisplay.from_predictions(y1_te, y1_prob, ax=axes[1])
    roc1.line_.set_color(NAVY)
    axes[1].plot([0, 1], [0, 1], '--', color='gray', lw=1)
    axes[1].set_title(f'ROC Curve  (AUC={auc1:.3f})')

    coef_df = pd.DataFrame({'Feature': FEAT_C1, 'Coef': m1.coef_[0]}
                           ).sort_values('Coef', key=abs, ascending=True)
    bar_c = [RED if c > 0 else GREEN for c in coef_df['Coef']]
    axes[2].barh(coef_df['Feature'], coef_df['Coef'], color=bar_c)
    axes[2].axvline(0, color='black', lw=0.8)
    axes[2].set_title('Feature Importance\n(Red = increases default risk)')
    add_bar_labels(axes[2], fmt='{:.2f}')
    plt.tight_layout()
    if show: plt.show()

    with open(f'{model_dir}/loan_default_model.pkl', 'wb') as f: pickle.dump(m1, f)
    with open(f'{model_dir}/scaler_c1.pkl', 'wb') as f:          pickle.dump(sc1, f)
    with open(f'{model_dir}/features_c1.pkl', 'wb') as f:        pickle.dump(FEAT_C1, f)
    print(f"Model saved → {model_dir}/loan_default_model.pkl")

    results['c1'] = {'accuracy': acc1, 'auc': auc1, 'model': m1, 'scaler': sc1, 'features': FEAT_C1}

    # ── C2. TRANSACTION FORECASTING (Linear Regression) ──────────────
    print("\n===== C2. TRANSACTION AMOUNT FORECASTING =====")
    print("Business Value: Improve financial planning")

    monthly_acc = transaction.groupby(
        ['account_id', 'year', 'month'])['amount'].mean().reset_index(name='avg_monthly_amt')
    monthly_acc['month_num'] = (monthly_acc['year'] - monthly_acc['year'].min()) * 12 + monthly_acc['month']

    C2 = monthly_acc.merge(txn_feat[['account_id', 'txn_count', 'avg_balance']],
                            on='account_id', how='left')
    C2 = C2.merge(card_flag[['account_id', 'has_card']], on='account_id', how='left')
    C2['has_card'] = C2['has_card'].fillna(0)
    C2 = C2.dropna(subset=['avg_monthly_amt'])

    FEAT_C2 = [f for f in ['month_num', 'txn_count', 'avg_balance', 'has_card'] if f in C2.columns]
    X2 = C2[FEAT_C2]
    y2 = C2['avg_monthly_amt']
    _require_rows(X2, "C2 transaction forecasting dataset",
                  "transaction['year']/['month'] are NaN for every row — the date column "
                  "in your transaction table likely didn't parse. Check the ⚠️ WARNING "
                  "from data_prep.py about transaction['Date'].")

    X2_tr, X2_te, y2_tr, y2_te = train_test_split(X2, y2, test_size=0.2, random_state=42)
    sc2 = StandardScaler()
    X2_tr_s = sc2.fit_transform(X2_tr)
    X2_te_s = sc2.transform(X2_te)

    m2 = LinearRegression()
    m2.fit(X2_tr_s, y2_tr)
    y2_pred = m2.predict(X2_te_s)
    mae2 = mean_absolute_error(y2_te, y2_pred)
    r2_2 = r2_score(y2_te, y2_pred)

    print(f"✅ MAE : {mae2:,.2f} CZK")
    print(f"✅ R²  : {r2_2:.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f'C2 — Transaction Forecasting  |  MAE={mae2:,.0f} CZK  R²={r2_2:.3f}',
                 fontsize=13, fontweight='bold')

    sample = min(1000, len(y2_te))
    axes[0].scatter(y2_te[:sample], y2_pred[:sample], color=TEAL, alpha=0.3, s=15)
    lim = max(y2_te.max(), y2_pred.max())
    axes[0].plot([0, lim], [0, lim], color=ORANGE, lw=2, linestyle='--', label='Perfect')
    axes[0].set_title('Actual vs Predicted Txn Amount')
    axes[0].set_xlabel('Actual (CZK)'); axes[0].set_ylabel('Predicted (CZK)')
    axes[0].legend()

    residuals = y2_te.values - y2_pred
    axes[1].hist(residuals, bins=40, color=NAVY, edgecolor='white')
    axes[1].axvline(0, color=RED, lw=2, linestyle='--')
    axes[1].set_title('Residuals Distribution')
    axes[1].set_xlabel('Actual − Predicted')
    plt.tight_layout()
    if show: plt.show()

    with open(f'{model_dir}/txn_forecast_model.pkl', 'wb') as f: pickle.dump(m2, f)
    with open(f'{model_dir}/scaler_c2.pkl', 'wb') as f:          pickle.dump(sc2, f)
    with open(f'{model_dir}/features_c2.pkl', 'wb') as f:        pickle.dump(FEAT_C2, f)
    print(f"Model saved → {model_dir}/txn_forecast_model.pkl")

    results['c2'] = {'mae': mae2, 'r2': r2_2, 'model': m2, 'scaler': sc2, 'features': FEAT_C2}

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run predictive modelling for the bank dataset.')
    parser.add_argument('--data-dir', default='.', help='Folder containing the raw CSV files')
    parser.add_argument('--model-dir', default='model', help='Folder to save trained models into')
    args = parser.parse_args()

    raw = load_raw_tables(args.data_dir)
    data = prepare_data(**raw)
    run_predictive_analysis(data, model_dir=args.model_dir, show=True)
