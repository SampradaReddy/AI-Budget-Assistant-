"""Charts with matplotlib + seaborn. Each function returns a Figure for st.pyplot().

We build figures with Figure() instead of plt.subplots() because pyplot keeps
global state, which misbehaves when Streamlit runs several sessions at once.
"""

import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from src.config import CURRENCY

sns.set_theme(style="whitegrid")
_money_axis = FuncFormatter(lambda value, _: f"{CURRENCY}{value:,.0f}")


def _empty(fig: Figure, ax, message: str = "No data yet") -> Figure:
    ax.text(0.5, 0.5, message, ha="center", va="center", color="gray")
    ax.set_axis_off()
    return fig


def category_bar(totals: pd.Series) -> Figure:
    fig = Figure(figsize=(6, 3.6), layout="constrained")
    ax = fig.subplots()
    if totals.empty:
        return _empty(fig, ax)
    sns.barplot(x=totals.values, y=totals.index, hue=totals.index, palette="viridis", legend=False, ax=ax)
    ax.xaxis.set_major_formatter(_money_axis)
    ax.set(xlabel="", ylabel="", title="Spending by category")
    return fig


def daily_line(daily: pd.Series) -> Figure:
    fig = Figure(figsize=(6, 3.6), layout="constrained")
    ax = fig.subplots()
    if daily.empty:
        return _empty(fig, ax)
    sns.lineplot(x=pd.to_datetime(daily.index), y=daily.values, marker="o", ax=ax)
    ax.yaxis.set_major_formatter(_money_axis)
    ax.set(xlabel="", ylabel="", title="Spending per day")
    fig.autofmt_xdate()
    return fig


def monthly_bar(monthly: pd.Series) -> Figure:
    fig = Figure(figsize=(6, 3.6), layout="constrained")
    ax = fig.subplots()
    if monthly.empty:
        return _empty(fig, ax)
    sns.barplot(x=monthly.index, y=monthly.values, color="#4c72b0", ax=ax)
    ax.yaxis.set_major_formatter(_money_axis)
    ax.set(xlabel="", ylabel="", title="Total per month")
    return fig


def budget_vs_actual(status: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(6, 3.6), layout="constrained")
    ax = fig.subplots()
    if status.empty:
        return _empty(fig, ax, "No budgets set")
    long = status.melt(id_vars="category", value_vars=["limit", "spent"], var_name="type", value_name="amount")
    sns.barplot(data=long, x="amount", y="category", hue="type", palette={"limit": "#b0b0b0", "spent": "#dd8452"}, ax=ax)
    ax.xaxis.set_major_formatter(_money_axis)
    ax.set(xlabel="", ylabel="", title="Budget vs actual (this month)")
    ax.legend(title="")
    return fig
