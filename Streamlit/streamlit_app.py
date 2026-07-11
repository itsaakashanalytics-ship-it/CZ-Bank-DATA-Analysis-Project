# ================================================================
# CZECHOSLOVAKIA BANK — STREAMLIT DASHBOARD
#
# Wraps data_prep.py, descriptive_analysis.py and predictive_analysis.py
# in an interactive app with 3 tabs:
#   1) Descriptive & Diagnostic EDA  (Section A + B, all charts + KPIs)
#   2) Predictive Models             (Section C, trains + evaluates models)
#   3) Try a Prediction               (live form using the trained models)
#
# Run with:  streamlit run streamlit_app.py
# ================================================================

import io
import os
import builtins
import contextlib

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from data_prep import load_raw_tables, load_raw_tables_sql, prepare_data, build_ml_base
from descriptive_analysis import run_descriptive_analysis
from predictive_analysis import run_predictive_analysis

st.set_page_config(page_title="Czech Bank Analytics", page_icon="🏦", layout="wide")

# Resolve paths relative to THIS FILE's location, not the process's working
# directory. Streamlit Cloud runs the app with the repo root as the working
# directory regardless of which subfolder the entry-point script lives in,
# so a plain relative path like "data" can silently point at the wrong
# place if streamlit_app.py isn't at the repo root.
APP_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Helper: redirect every plt.show() call to st.pyplot() ───────────
def _st_show():
    fig = plt.gcf()
    st.pyplot(fig, width='stretch')
    plt.close(fig)


# ── Helper: run a function, rendering its print() output INLINE ─────
# The old version captured every print() into a buffer and only displayed
# it after the whole function (and all its plt.show() charts) had already
# finished — so the page showed "all charts, then all text" instead of
# each KPI/table appearing right above its matching chart, like in the
# notebook. This patches builtins.print so each call renders to the page
# immediately, in the exact order the analysis script executes it in.
def _run_capturing_output(func, *args, **kwargs):
    buf = io.StringIO()
    original_print = builtins.print

    def _live_print(*args_, **kwargs_):
        sep = kwargs_.get('sep', ' ')
        end = kwargs_.get('end', '\n')
        text = sep.join(str(a) for a in args_)
        buf.write(text + end)
        st.text(text)  # renders immediately, in document order

    builtins.print = _live_print
    try:
        result = func(*args, **kwargs)
    finally:
        builtins.print = original_print  # always restore, even on error
    return result, buf.getvalue()


@st.cache_data(show_spinner="Loading & preparing data from CSV...")
def _load_data_csv(data_dir, sep):
    raw = load_raw_tables(data_dir, sep=sep)
    return prepare_data(**raw)


@st.cache_data(show_spinner="Loading & preparing data from SQL Server...")
def _load_data_sql(server, database, trusted_connection, username, password,
                    driver, schema, table_overrides, dialect, port):
    raw = load_raw_tables_sql(
        server=server, database=database, trusted_connection=trusted_connection,
        username=username or None, password=password or None,
        driver=driver, schema=schema or None,
        tables=table_overrides or None, dialect=dialect, port=port,
    )
    return prepare_data(**raw)


def _secret(key, default=""):
    """Reads a value from st.secrets if present, else falls back to default.
    Lets you predefine connection details in .streamlit/secrets.toml (locally)
    or the Streamlit Cloud 'Secrets' settings, instead of retyping them."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ── SIDEBAR ───────────────────────────────────────────────────────
st.sidebar.title("🏦 Czech Bank Analytics")

DEFAULT_DATA_DIR = os.path.join(APP_DIR, "data")   # the folder committed to the repo via export_sql_to_csv.py
DEFAULT_SEP = ";"

if "data" not in st.session_state:
    st.session_state.data = None
if "pred_results" not in st.session_state:
    st.session_state.pred_results = None
if "load_error" not in st.session_state:
    st.session_state.load_error = None

# Auto-load the committed CSVs on first run — no button click needed.
if st.session_state.data is None and st.session_state.load_error is None:
    try:
        st.session_state.data = _load_data_csv(DEFAULT_DATA_DIR, DEFAULT_SEP)
    except Exception as e:
        st.session_state.load_error = str(e)

model_dir = st.sidebar.text_input("Model output folder", value="model")

with st.sidebar.expander("⚙️ Advanced: change data source"):
    st.caption("Only needed if the committed CSVs aren't present, or you want "
               "to point at a different folder or a live SQL Server instead.")
    source = st.radio("Data source", ["CSV files", "SQL Server"], index=0, key="adv_source")

    if source == "CSV files":
        data_dir = st.text_input("Data folder (raw CSVs)", value=DEFAULT_DATA_DIR)
        sep = st.selectbox("CSV separator", [";", ","], index=0)

        if st.button("📥 Reload from this folder", type="primary"):
            try:
                st.session_state.data = _load_data_csv(data_dir, sep)
                st.session_state.load_error = None
                st.success("Data loaded successfully.")
            except Exception as e:
                st.session_state.load_error = str(e)
                st.error(f"Failed to load data: {e}")

    else:  # SQL Server
        dialect = st.radio(
            "Connection method", ["pyodbc (local/Windows)", "pymssql (cloud-friendly)"], index=0,
            help="Use pymssql when deploying to Streamlit Community Cloud — it needs no "
                 "OS-level ODBC driver install. pyodbc supports Windows/Trusted auth but "
                 "only works when the app runs on a machine with the driver + domain access.",
        )
        dialect_value = 'pymssql' if dialect.startswith('pymssql') else 'pyodbc'

        server = st.text_input("Server", value=_secret("sql_server"),
                                placeholder="e.g. MYSERVER\\SQLEXPRESS or myserver.database.windows.net")
        database = st.text_input("Database", value=_secret("sql_database"))
        port = st.number_input("Port", value=int(_secret("sql_port", 1433) or 1433), step=1)
        schema = st.text_input("Schema (optional)", value=_secret("sql_schema", "dbo"),
                                help="Leave blank if your tables aren't schema-qualified.")

        if dialect_value == 'pyodbc':
            auth_mode = st.radio("Authentication", ["Windows / Trusted", "SQL login"], index=0)
            trusted = auth_mode == "Windows / Trusted"
        else:
            st.caption("pymssql requires a SQL Server login (Windows/Trusted auth isn't supported).")
            trusted = False

        username = password = ""
        if not trusted:
            username = st.text_input("Username", value=_secret("sql_username"))
            password = st.text_input("Password", value=_secret("sql_password"), type="password")
        driver = st.text_input("ODBC driver", value="ODBC Driver 17 for SQL Server",
                                disabled=(dialect_value == 'pymssql'))

        with st.expander("Override table names (optional)"):
            st.caption("Only fill in tables whose name differs from the default.")
            table_overrides = {}
            for logical in ['account', 'client', 'district', 'disp', 'card', 'loan', 'orders', 'transaction']:
                override = st.text_input(logical, value="", key=f"tbl_{logical}")
                if override.strip():
                    table_overrides[logical] = override.strip()

        if st.button("📥 Connect & Load", type="primary"):
            if not server or not database:
                st.error("Please enter both Server and Database.")
            else:
                try:
                    st.session_state.data = _load_data_sql(
                        server, database, trusted,
                        username, password, driver, schema, table_overrides,
                        dialect_value, int(port),
                    )
                    st.session_state.load_error = None
                    st.success("Data loaded successfully from SQL Server.")
                except Exception as e:
                    st.session_state.load_error = str(e)
                    st.error(f"Failed to load data: {e}")

st.title("Czechoslovakia Bank — Analytics Dashboard")
st.caption("Descriptive, diagnostic & predictive analysis, in one interactive app.")

if st.session_state.data is None:
    st.error(
        f"Couldn't auto-load data from `{DEFAULT_DATA_DIR}`."
        + (f"\n\nError: {st.session_state.load_error}" if st.session_state.load_error else "")
    )
    st.info("👈 Open **⚙️ Advanced: change data source** in the sidebar to point at "
            "the right folder or connect to SQL Server manually.")
    st.stop()

data = st.session_state.data

tab_desc, tab_pred, tab_try = st.tabs(
    ["📊 Descriptive & Diagnostic EDA", "🤖 Predictive Models", "🔮 Try a Prediction"]
)

# ── TAB 1 — DESCRIPTIVE & DIAGNOSTIC EDA (Sections A + B) ──────────
with tab_desc:
    st.header("Sections A & B — Descriptive and Diagnostic EDA")
    st.write(
        "Runs every chart from `descriptive_analysis.py` (customer demographics, "
        "accounts, transactions, loans, cards, districts, and the diagnostic "
        "deep-dives) directly in this page, with value labels on every bar chart."
    )
   
    plt.show = _st_show  # redirect this run's plt.show() calls into the page
    with st.spinner("Crunching numbers and drawing charts..."):
        kpis, log_text = _run_capturing_output(run_descriptive_analysis, data, show=True)
    st.session_state.desc_kpis = kpis

    st.subheader("Key KPIs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Clients", f"{kpis['total_clients']:,}")
    c2.metric("Total Accounts", f"{kpis['total_accounts']:,}")
    c3.metric("Total Transactions", f"{kpis['total_txns']:,}")
    c4.metric("Total Loans", f"{kpis['total_loans']:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Loan Default Rate", f"{kpis['default_rate']:.2f}%")
    c6.metric("Card Penetration", f"{kpis['card_penetration']:.1f}%")
    c7.metric("Dormant Accounts", f"{kpis['dormant_rate']:.1f}%")
    c8.metric("High-Debit Accounts", f"{kpis['high_debit_rate']:.1f}%")

# ── TAB 2 — PREDICTIVE MODELS (Section C) ──────────────────────────
with tab_pred:
    st.header("Section C — Predictive Modelling")
    st.write(
        "Trains and evaluates the three models from `predictive_analysis.py`: "
        "loan default prediction, transaction forecasting, and card adoption "
        "prediction. Models are pickled to the model folder for reuse."
    )

    plt.show = _st_show
    with st.spinner("Training models..."):
        results, log_text = _run_capturing_output(
            run_predictive_analysis, data, model_dir=model_dir, show=True
        )
    st.session_state.pred_results = results

    st.subheader("Model Performance")
    c1, c2, c3 = st.columns(3)
    c1.metric("C1 — Loan Default AUC", f"{results['c1']['auc']:.3f}",
               help=f"Accuracy: {results['c1']['accuracy']*100:.1f}%")
    c2.metric("C2 — Txn Forecast R²", f"{results['c2']['r2']:.3f}",
               help=f"MAE: {results['c2']['mae']:,.0f} CZK")

# ── TAB 3 — TRY A PREDICTION (live form using trained models) ──────
with tab_try:
    st.header("Try a Live Prediction")
    if st.session_state.pred_results is None:
        st.warning("Train the models in the **Predictive Models** tab first.")
    else:
        results = st.session_state.pred_results
        model_choice = st.selectbox(
            "Choose a model",
            ["C1 — Loan Default Risk", "C3 — Card Adoption Likelihood"]
        )

        if model_choice.startswith("C1"):
            info = results['c1']
            st.write(f"Features used: `{info['features']}`")
            with st.form("c1_form"):
                inputs = {}
                cols = st.columns(2)
                for i, feat in enumerate(info['features']):
                    with cols[i % 2]:
                        inputs[feat] = st.number_input(feat, value=0.0, step=1.0)
                submitted = st.form_submit_button("Predict Default Risk")
            if submitted:
                X = pd.DataFrame([inputs])[info['features']]
                X_s = info['scaler'].transform(X)
                prob = info['model'].predict_proba(X_s)[0, 1]
                st.metric("Predicted Default Probability", f"{prob*100:.1f}%")
                st.progress(min(max(prob, 0.0), 1.0))
                if prob > 0.5:
                    st.error("⚠️ Model flags this loan as HIGH RISK of default.")
                else:
                    st.success("✅ Model flags this loan as LOW RISK of default.")

            if submitted:
                X = pd.DataFrame([inputs])[info['features']]
                X_s = info['scaler'].transform(X)
                prob = info['model'].predict_proba(X_s)[0, 1]
                st.metric("Predicted Card Adoption Probability", f"{prob*100:.1f}%")
                st.progress(min(max(prob, 0.0), 1.0))
                if prob > 0.5:
                    st.success("💳 Model predicts this customer is LIKELY to adopt a card.")
                else:
                    st.info("Model predicts this customer is UNLIKELY to adopt a card.")
