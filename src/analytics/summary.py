"""Number crunching with pandas. Functions take a DataFrame and return a DataFrame/Series/number."""

from datetime import date

import pandas as pd


def filter_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]


def current_month(df: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    today = today or date.today()
    return filter_month(df, today.year, today.month)


def category_totals(df: pd.DataFrame) -> pd.Series:
    """Total spent per category, biggest first."""
    if df.empty:
        return pd.Series(dtype=float, name="amount")
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)


def daily_totals(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float, name="amount")
    return df.groupby(df["date"].dt.date)["amount"].sum().sort_index()


def monthly_totals(df: pd.DataFrame) -> pd.Series:
    """Total per month, indexed by strings like '2026-10'."""
    if df.empty:
        return pd.Series(dtype=float, name="amount")
    return df.groupby(df["date"].dt.strftime("%Y-%m"))["amount"].sum().sort_index()


def available_months(df: pd.DataFrame) -> list[str]:
    """['2026-10', '2026-09', ...] newest first."""
    return sorted(monthly_totals(df).index, reverse=True)


def budget_status(month_df: pd.DataFrame, budgets: dict[str, float]) -> pd.DataFrame:
    """One row per budgeted category: limit, spent, remaining, percent used."""
    columns = ["category", "limit", "spent", "remaining", "percent_used"]
    if not budgets:
        return pd.DataFrame(columns=columns)

    spent = category_totals(month_df)
    rows = []
    for category, limit in budgets.items():
        used = float(spent.get(category, 0.0))
        rows.append(
            {
                "category": category,
                "limit": limit,
                "spent": used,
                "remaining": limit - used,
                "percent_used": round(used / limit * 100, 1),
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values("percent_used", ascending=False).reset_index(drop=True)
