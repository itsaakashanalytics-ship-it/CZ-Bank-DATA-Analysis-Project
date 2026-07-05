# Czechoslovakia Bank Analysis — Project Structure

Your original single-file script has been split into reusable modules, with
**data labels added to every bar/barh chart**, plus a new **Streamlit app**.

## Files

| File                     | Purpose                                                                 |
|--------------------------|--------------------------------------------------------------------------|
| `data_prep.py`           | Loads the 8 raw CSVs, cleans them, engineers features, builds joins.    |
| `chart_utils.py`         | `add_bar_labels()` helper — adds value labels to any bar/barh chart.    |
| `descriptive_analysis.py`| **Section A + B**: descriptive & diagnostic EDA (all the `axes[...]` charts). |
| `predictive_analysis.py` | **Section C**: trains, evaluates, and pickles the 3 ML models.         |
| `main.py`                | Runs both scripts back-to-back and prints the final KPI summary.       |
| `streamlit_app.py`       | Interactive dashboard: EDA tab, model-training tab, live prediction tab.|

## ⚠️ One thing to check: your data file names

`data_prep.py` assumes the classic "Berka" dataset file names
(`account.csv`, `client.csv`, `district.csv`, `disp.csv`, `card.csv`,
`loan.csv`, `order.csv`, `trans.csv`) separated by `;`. If your files are
named differently, edit `DEFAULT_FILES` at the top of `data_prep.py`, or
pass your own dict to `load_raw_tables(data_dir, files={...})`.

## Deploying to Streamlit Community Cloud

The error you're seeing means the app isn't in a GitHub repo yet — Streamlit
Cloud deploys straight from a repo, not from local files. Here's the full path:

### 1. Push your code to GitHub

```bash
cd path/to/your/files          # the folder with streamlit_app.py etc.
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
(Create the empty repo on github.com first if you haven't.)

Make sure `requirements.txt` and `.gitignore` (both included here) are in
the repo root alongside `streamlit_app.py`, `data_prep.py`,
`descriptive_analysis.py`, `predictive_analysis.py`, `chart_utils.py`, and
`main.py`.

### 2. Deploy on share.streamlit.io

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app** → pick your repo/branch → set **Main file path** to `streamlit_app.py`.
3. Click **Deploy**.

### 3. ⚠️ Switch your SQL connection method — Windows auth won't work here

Streamlit Community Cloud runs your app on a Linux container that has no
access to your Windows domain, so **Windows/Trusted authentication cannot
work once deployed**. In the app's sidebar, switch:
- **Connection method → "pymssql (cloud-friendly)"** — needs no OS driver install.
- **Authentication → SQL login** — you'll need a SQL Server username/password
  (ask your DBA to create one if you don't have one).

Also make sure your SQL Server is reachable from the public internet (Azure
SQL is by default; an on-prem server needs a firewall rule opening port 1433
to Streamlit Cloud's outbound IPs, or a VPN/tunnel).

### 4. Store credentials in Secrets, not in the sidebar

Retyping your password every time the app restarts is inconvenient and
insecure. Instead, copy `secrets.toml.example` → fill in your real values →
paste its contents into your app's **Settings → Secrets** on Streamlit Cloud
(or save it locally as `.streamlit/secrets.toml` for local runs — it's
already git-ignored). The sidebar's Server/Database/Username/Password
fields will auto-fill from these secrets, and you can still override them
by hand for one-off connections.

## Using SQL Server instead of CSVs

Since your 8 tables (including 6 years of merged transactions) live in SQL
Server, use `load_raw_tables_sql()` from `data_prep.py` instead of
`load_raw_tables()`. It needs `sqlalchemy` + `pyodbc`, plus the ODBC driver
installed on the machine running the code:

```bash
pip install sqlalchemy pyodbc
```

**Windows/Trusted authentication (your setup):**
```python
from data_prep import load_raw_tables_sql, prepare_data

raw = load_raw_tables_sql(
    server="MYSERVER\\SQLEXPRESS",   # or "myserver.database.windows.net"
    database="BankDB",
    schema="dbo",                    # or None if tables aren't schema-qualified
    trusted_connection=True,         # Windows auth — no username/password needed
)
data = prepare_data(**raw)
```

If any of your 8 table names differ from the defaults (`account`, `client`,
`district`, `disp`, `card`, `loan`, `order`, `transaction`), pass overrides:
```python
raw = load_raw_tables_sql(
    server="MYSERVER\\SQLEXPRESS", database="BankDB",
    tables={"transaction": "transactions_all_years"},
)
```

**From the CLI:**
```bash
python main.py --source sql --sql-server "MYSERVER\SQLEXPRESS" --sql-database BankDB
```

**In the Streamlit app:** pick **SQL Server** in the sidebar's "Data source"
radio button, fill in Server/Database (Windows/Trusted auth is preselected),
and optionally expand "Override table names" if your schema differs.

> Note: Windows/Trusted authentication only works when the app runs *on* a
> machine that's part of the same Windows domain/session as SQL Server (e.g.
> your local machine or a domain-joined server) — it won't work if you
> later deploy the Streamlit app to a Linux host or Streamlit Community
> Cloud. In that case you'd switch to a SQL login instead.

## Running as scripts

```bash
pip install pandas numpy matplotlib seaborn scikit-learn streamlit

python main.py --data-dir ./data --model-dir ./model
# or run each stage independently:
python descriptive_analysis.py --data-dir ./data
python predictive_analysis.py --data-dir ./data --model-dir ./model
```

## Running the Streamlit app

```bash
streamlit run streamlit_app.py
```

Then in the sidebar: set your data folder → **Load & Prepare Data** →
open the **Descriptive & Diagnostic EDA** tab and click **Run** → open the
**Predictive Models** tab and click **Train & Evaluate** → try live
predictions in the **Try a Prediction** tab.

## What changed vs. the original script

- Every `ax.bar(...)` / `ax.barh(...)` / `DataFrame.plot(kind='bar')` chart
  now has value labels added via `add_bar_labels()` (uses `ax.bar_label`
  under the hood).
- All data loading/cleaning/joins moved into `data_prep.py` so it's written
  once and shared by every script — no more copy-pasted prep code.
- Descriptive (`Section A` + `Section B`) and predictive (`Section C`) logic
  each live in their own file behind a `run_*_analysis(data)` function, so
  they can be imported and reused (e.g., by the Streamlit app) instead of
  only running top-to-bottom as a notebook-style script.
