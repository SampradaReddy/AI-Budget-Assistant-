"""Add expenses one at a time or from a CSV, and delete mistakes."""

from datetime import date

import pandas as pd
import streamlit as st

from src.config import CATEGORIES, money
from src.database import crud
from src.database.db import init_db
from src.ml import categorizer

st.set_page_config(page_title="Log Expense", page_icon="📝", layout="wide")
init_db()

AUTO = "Auto-detect (ML)"

st.title("📝 Log Expense")

# ---- Single expense ----
with st.form("add_expense", clear_on_submit=True):
    description = st.text_input("Description", placeholder="e.g. Swiggy order biryani")
    col1, col2, col3 = st.columns(3)
    amount = col1.number_input("Amount", min_value=0.0, step=10.0)
    day = col2.date_input("Date", value=date.today(), max_value=date.today())
    choice = col3.selectbox("Category", [AUTO] + CATEGORIES)
    submitted = st.form_submit_button("Add expense", type="primary")

if submitted:
    try:
        if choice == AUTO:
            category, confidence = categorizer.predict(description)
            note = f" (auto-detected, {confidence:.0%} confident)"
        else:
            category, note = choice, ""
        crud.add_expense(day, description, amount, category)
        st.success(f"Saved {money(amount)} under **{category}**{note}.")
    except ValueError as error:
        st.error(str(error))

# ---- CSV import ----
with st.expander("Import from CSV"):
    st.write("Columns needed: `date`, `description`, `amount`. A `category` column is optional; blanks are auto-detected.")
    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded is not None:
        try:
            csv = pd.read_csv(uploaded)
            csv.columns = [c.strip().lower() for c in csv.columns]
            missing = {"date", "description", "amount"} - set(csv.columns)
            if missing:
                st.error(f"Missing column(s): {', '.join(sorted(missing))}")
            else:
                csv["date"] = pd.to_datetime(csv["date"], errors="coerce").dt.date
                csv["amount"] = pd.to_numeric(csv["amount"], errors="coerce")
                csv = csv.dropna(subset=["date", "description", "amount"])
                csv = csv[csv["amount"] > 0]
                if "category" not in csv.columns:
                    csv["category"] = None
                needs_guess = ~csv["category"].isin(CATEGORIES)
                csv.loc[needs_guess, "category"] = categorizer.predict_many(
                    csv.loc[needs_guess, "description"].astype(str).tolist()
                )
                st.dataframe(csv[["date", "description", "amount", "category"]], hide_index=True)
                if st.button(f"Import {len(csv)} rows"):
                    rows = csv[["date", "description", "amount", "category"]].to_dict("records")
                    crud.add_expenses_bulk(rows)
                    st.success(f"Imported {len(rows)} expenses.")
        except Exception as error:  # a bad file shouldn't crash the page
            st.error(f"Couldn't read that file: {error}")

# ---- Existing expenses ----
st.subheader("All expenses")
df = crud.get_expenses_df()
if df.empty:
    st.caption("Nothing logged yet.")
else:
    shown = df.copy()
    shown["date"] = shown["date"].dt.strftime("%d %b %Y")
    st.dataframe(shown, hide_index=True)

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    to_delete = col1.selectbox(
        "Delete an expense",
        df["id"],
        format_func=lambda i: "#{} — {} — {}".format(
            i, df.loc[df["id"] == i, "description"].iloc[0], money(df.loc[df["id"] == i, "amount"].iloc[0])
        ),
    )
    if col2.button("Delete"):
        crud.delete_expense(int(to_delete))
        st.rerun()
