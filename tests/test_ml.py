from datetime import date

import pandas as pd
import pytest

from src.config import CATEGORIES
from src.ml import categorizer
from src.ml.forecaster import forecast_month_end


@pytest.mark.parametrize(
    "description, expected",
    [
        ("zomato order", "Food"),
        ("uber to college", "Transport"),
        ("netflix", "Entertainment"),
        ("electricity bill", "Bills"),
        ("hostel rent", "Rent"),
    ],
)
def test_categorizer_obvious_cases(description, expected):
    category, confidence = categorizer.predict(description)
    assert category == expected
    assert 0 <= confidence <= 1


def test_categorizer_handles_empty_and_unknown_text():
    assert categorizer.predict("")[0] == "Other"
    assert categorizer.predict("qwxzv")[0] in CATEGORIES


def _expenses(rows):
    return pd.DataFrame({"date": pd.to_datetime([r[0] for r in rows]), "amount": [r[1] for r in rows]})


def test_forecast_steady_spending():
    # 100 a day for the first 10 days of a 31-day month -> about 3100.
    df = _expenses([(f"2026-10-{day:02d}", 100) for day in range(1, 11)])
    result = forecast_month_end(df, today=date(2026, 10, 10))
    assert result["spent_so_far"] == 1000
    assert result["projected_total"] == pytest.approx(3100, rel=0.01)


def test_forecast_early_month_uses_typical_day():
    df = _expenses([("2026-10-01", 200), ("2026-10-02", 400)])
    result = forecast_month_end(df, today=date(2026, 10, 2))
    assert result["projected_total"] == pytest.approx(600 + 300 * 29)
    assert "typical" in result["method"]


def test_forecast_early_month_rent_is_not_multiplied():
    # September: 100 a day. October 1st: rent. The forecast should be rent + ~100 a day, not rent x 31.
    september = [(f"2026-09-{day:02d}", 100) for day in range(1, 31)]
    df = _expenses(september + [("2026-10-01", 6000), ("2026-10-02", 100)])
    result = forecast_month_end(df, today=date(2026, 10, 2))
    assert result["projected_total"] == pytest.approx(6100 + 100 * 29)


def test_forecast_never_below_spent_and_handles_empty():
    # One big payment on day 1, then nothing: the trend line is flat, forecast = spent.
    df = _expenses([("2026-10-01", 6000)])
    result = forecast_month_end(df, today=date(2026, 10, 20))
    assert result["projected_total"] >= result["spent_so_far"] == 6000

    empty = pd.DataFrame({"date": pd.to_datetime([]), "amount": []})
    assert forecast_month_end(empty)["projected_total"] == 0
