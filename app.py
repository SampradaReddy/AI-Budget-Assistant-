"""Home page / dashboard.  Run with:  streamlit run app.py"""

from datetime import date

import streamlit as st

from src import sample_data
from src.analytics import charts, summary
from src.config import money
from src.database import crud
from src.database.db import init_db
from src.ml.forecaster import forecast_month_end

st.set_page_config(page_title="AI Budget Assistant", page_icon="💰", layout="wide")
init_db()

st.title("💰 AI Budget Assistant")
st.caption(f"Overview for {date.today():%B %Y}")

df = crud.get_expenses_df()
budgets = crud.get_budgets()

if df.empty:
    st.info("No expenses yet. Log your first one from **Log Expense** in the sidebar, or load sample data to explore.")
    if st.button("Load sample data"):
        added = sample_data.load()
        st.success(f"Added {added} sample expenses.")
        st.rerun()
    st.stop()

month_df = summary.current_month(df)
forecast = forecast_month_end(df)
total_budget = sum(budgets.values())
spent = forecast["spent_so_far"]

# ---- Headline numbers ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Spent this month", money(spent))
col2.metric("Monthly budget", money(total_budget) if total_budget else "Not set")
col3.metric("Remaining", money(total_budget - spent) if total_budget else "—")
col4.metric(
    "Projected month-end",
    money(forecast["projected_total"]),
    # The +/- sign at the front is what tells Streamlit which way the arrow points.
    delta=f"{forecast['projected_total'] - total_budget:+,.0f} vs budget" if total_budget else None,
    delta_color="inverse",  # going over budget should show red, not green
)

if total_budget and forecast["projected_total"] > total_budget:
    st.warning(
        f"At this pace you'll overshoot your budget by about "
        f"{money(forecast['projected_total'] - total_budget)} this month."
    )

# ---- Charts ----
left, right = st.columns(2)
left.pyplot(charts.category_bar(summary.category_totals(month_df)))
right.pyplot(charts.daily_line(summary.daily_totals(month_df)))

# ---- Recent expenses ----
st.subheader("Recent expenses")
recent = df.head(10).drop(columns="id").copy()
recent["date"] = recent["date"].dt.strftime("%d %b %Y")
st.dataframe(recent, hide_index=True)
