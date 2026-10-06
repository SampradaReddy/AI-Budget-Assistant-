"""Predict how much will be spent by the end of the current month.

Method: add up spending day by day (a running total), fit a straight line through
it with linear regression, and read off where the line lands on the last day of
the month. In the first few days a line is unreliable, so we fall back to
"spent so far + a typical day x days left". "Typical" is the median, not the
mean, so one big payment like rent doesn't get multiplied across the month.

Known limit: a large one-off purchase mid-month tilts the line upward. Good
enough for a first version; a natural upgrade is forecasting fixed and variable
spending separately.
"""

import calendar
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

MIN_DAYS_FOR_REGRESSION = 5


def forecast_month_end(df: pd.DataFrame, today: date | None = None) -> dict:
    """df: expenses with `date` and `amount` columns (any months; we filter here)."""
    today = today or date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    result = {
        "spent_so_far": 0.0,
        "projected_total": 0.0,
        "days_elapsed": today.day,
        "days_in_month": days_in_month,
        "method": "no data",
    }
    if df.empty:
        return result

    this_month = df[(df["date"].dt.year == today.year) & (df["date"].dt.month == today.month)]
    this_month = this_month[this_month["date"].dt.day <= today.day]
    if this_month.empty:
        return result

    # Total per day of month, with 0 for days that had no spending.
    daily = this_month.groupby(this_month["date"].dt.day)["amount"].sum()
    daily = daily.reindex(range(1, today.day + 1), fill_value=0.0)
    cumulative = daily.cumsum()
    spent = float(cumulative.iloc[-1])
    result["spent_so_far"] = spent

    if today.day >= MIN_DAYS_FOR_REGRESSION:
        days = np.array(cumulative.index).reshape(-1, 1)
        line = LinearRegression().fit(days, cumulative.values)
        projected = float(line.predict([[days_in_month]])[0])
        result["method"] = "linear regression on running total"
    else:
        days_left = days_in_month - today.day
        projected = spent + _typical_daily_spend(df, today, daily) * days_left
        result["method"] = "typical daily spend (too early in the month for a trend)"

    # A forecast can never be lower than what has already been spent.
    result["projected_total"] = max(projected, spent)
    return result


def _typical_daily_spend(df: pd.DataFrame, today: date, daily_this_month: pd.Series) -> float:
    """Median spend per day over the 60 days before this month; this month's median if there's no history."""
    first_of_month = today.replace(day=1)
    month_start = pd.Timestamp(first_of_month)
    cutoff = pd.Timestamp(first_of_month - timedelta(days=60))
    history = df[(df["date"] < month_start) & (df["date"] >= cutoff)]
    if history.empty:
        return float(daily_this_month.median())

    per_day = history.groupby(history["date"].dt.normalize())["amount"].sum()
    # Days with no spending count as 0, starting from the first day we have data for.
    days_covered = (month_start - per_day.index.min()).days
    zero_days = [0.0] * (days_covered - len(per_day))
    return float(np.median(list(per_day.values) + zero_days))
