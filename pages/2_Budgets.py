"""Set a monthly limit per category and see how this month is tracking."""

import streamlit as st

from src.analytics import charts, summary
from src.config import CATEGORIES, CURRENCY, money
from src.database import crud
from src.database.db import init_db

st.set_page_config(page_title="Budgets", page_icon="🎯", layout="wide")
init_db()

st.title("🎯 Budgets")

budgets = crud.get_budgets()

with st.form("budgets"):
    st.write("Monthly limit per category. Leave at 0 for no limit.")
    columns = st.columns(3)
    new_limits = {}
    for i, category in enumerate(CATEGORIES):
        new_limits[category] = columns[i % 3].number_input(
            f"{category} ({CURRENCY})", min_value=0.0, step=100.0, value=float(budgets.get(category, 0.0))
        )
    if st.form_submit_button("Save budgets", type="primary"):
        for category, limit in new_limits.items():
            crud.set_budget(category, limit)
        st.success("Budgets saved.")
        budgets = crud.get_budgets()

st.subheader("This month")
status = summary.budget_status(summary.current_month(crud.get_expenses_df()), budgets)

if status.empty:
    st.caption("Set at least one budget above to see tracking.")
else:
    for row in status.itertuples():
        label = f"**{row.category}** — {money(row.spent)} of {money(row.limit)}"
        if row.remaining < 0:
            label += f" · over by {money(-row.remaining)} ⚠️"
        st.progress(min(row.percent_used / 100, 1.0), text=label)
    st.pyplot(charts.budget_vs_actual(status))
