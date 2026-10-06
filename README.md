# AI Budget Assistant

A personal budgeting app built with Streamlit. Log expenses, let a small ML model categorise them, track budgets, see a month-end forecast, and ask a Gemini-powered assistant about your spending.

## Features

- **Log expenses** one at a time or by CSV import, with automatic categorisation (scikit-learn)
- **Budgets** per category with progress tracking
- **Insights**: category, daily and monthly charts (matplotlib + seaborn)
- **Forecast** of month-end spending (linear regression)
- **Assistant**: chat with Gemini about your numbers (google-genai + LangChain)
- Data stored locally in SQLite through SQLAlchemy

## Setup

Requires Python 3.11.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 2. Install packages
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Add your Gemini key (only needed for the Assistant page)
copy .env.example .env         # Windows (Mac/Linux: cp .env.example .env)
# then open .env and paste your key from https://aistudio.google.com/apikey

# 4. Run
streamlit run app.py
```

On first launch, click **Load sample data** to explore with fake expenses, or start logging your own.

In VS Code: open the folder, press `Ctrl+Shift+P` → *Python: Select Interpreter* → pick the one inside `venv`. `F5` runs the app with the debugger.

If the Assistant says the model wasn't found, run `python -m scripts.list_models` and put one of the printed names in `.env` as `GEMINI_MODEL`.

## Project structure

```
app.py                     Dashboard (home page)
pages/
  1_Log_Expense.py         Add / import / delete expenses
  2_Budgets.py             Set limits, track this month
  3_Insights.py            Charts and forecast
  4_Assistant.py           Gemini chat
src/
  config.py                Settings, categories, .env loading
  sample_data.py           Fake data generator
  database/
    db.py                  Engine and session
    models.py              Expense and Budget tables
    crud.py                Every read/write to the database
  ml/
    categorizer.py         Description -> category (TF-IDF + logistic regression)
    forecaster.py          Month-end forecast (linear regression)
  analytics/
    summary.py             pandas aggregations
    charts.py              matplotlib/seaborn figures
  ai/
    gemini_client.py       The only file that calls Gemini
    assistant.py           LangChain prompt -> Gemini pipeline
data/
  training_data.csv        Labelled examples for the categoriser
scripts/
  seed_db.py               python -m scripts.seed_db
  list_models.py           python -m scripts.list_models
tests/                     pytest tests
```

Pages only call functions in `src/`. Nothing in `src/` imports Streamlit, so the logic can be tested and reused without the UI.

## How the main pieces work

**Categoriser.** Trains on `data/training_data.csv` (about 320 labelled descriptions) each time the app starts, which takes a fraction of a second. If its confidence is under 25% it answers "Other". To make it better, add rows to the CSV in the same `description,category` format.

**Forecast.** Builds a running total of this month's spending and fits a straight line through it. In the first four days of a month there isn't enough data for a line, so it uses spent-so-far plus a typical day (median of the last 60 days) for each remaining day.

**Assistant.** Python calculates the totals; Gemini only explains them. The prompt contains aggregated numbers (totals, budgets, forecast), never individual transactions. The sidebar on the Assistant page shows exactly what is sent.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Tests use a temporary database, so they never touch your real data.

## Known limitations

- The categoriser's training data is small and hand-written. It handles common descriptions well and will misfire on unfamiliar ones.
- The forecast is a straight-line estimate. A big one-off purchase mid-month skews it.
- Single user, no login. Everything is in one local SQLite file (`data/budget.db`).
- `requests` is installed but not used yet. `langchain-community` is used only for chat history, and that package now prints a notice that it is being retired.
- General budgeting guidance only, not financial advice.
