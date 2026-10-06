"""Charts for any month, plus the month-end forecast."""

import streamlit as st

from src.analytics import charts, summary
from src.config import money
from src.database import crud
from src.database.db import init_db
from src.ml.forecaster import forecast_month_end

st.set_page_config(page_title="Insights", page_icon="📊", layout="wide")
init_db()

st.title("📊 Insights")

df = crud.get_expenses_df()
if df.empty:
    st.info("Log some expenses first.")
    st.stop()

# ---- Forecast (always about the current month) ----
st.subheader("Month-end forecast")
forecast = forecast_month_end(df)
col1, col2, col3 = st.columns(3)
col1.metric("Spent so far", money(forecast["spent_so_far"]))
col2.metric("Projected total", money(forecast["projected_total"]))
col3.metric("Day of month", f"{forecast['days_elapsed']} / {forecast['days_in_month']}")
st.caption(f"Method: {forecast['method']}. A rough estimate, not a guarantee.")

# ---- Pick a month to explore ----
st.subheader("Explore a month")
month = st.selectbox("Month", summary.available_months(df))
year_number, month_number = (int(part) for part in month.split("-"))
month_df = summary.filter_month(df, year_number, month_number)

col1, col2, col3 = st.columns(3)
col1.metric("Total", money(month_df["amount"].sum()))
col2.metric("Transactions", len(month_df))
col3.metric("Average per transaction", money(month_df["amount"].mean()))

left, right = st.columns(2)
left.pyplot(charts.category_bar(summary.category_totals(month_df)))
right.pyplot(charts.daily_line(summary.daily_totals(month_df)))

left, right = st.columns(2)
left.pyplot(charts.monthly_bar(summary.monthly_totals(df)))
with right:
    st.write("**Biggest expenses**")
    biggest = month_df.nlargest(5, "amount")[["date", "description", "amount", "category"]].copy()
    biggest["date"] = biggest["date"].dt.strftime("%d %b")
    st.dataframe(biggest, hide_index=True)
