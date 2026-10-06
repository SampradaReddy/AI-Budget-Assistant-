from datetime import date

import pandas as pd

from src.ai.assistant import build_context
from src.analytics import summary


def _df():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-09-15", "2026-10-01", "2026-10-02", "2026-10-03"]),
            "description": ["Old", "Lunch", "Dinner", "Uber"],
            "amount": [1000.0, 100.0, 300.0, 200.0],
            "category": ["Shopping", "Food", "Food", "Transport"],
        }
    )


def test_filter_month_and_category_totals():
    october = summary.filter_month(_df(), 2026, 10)
    totals = summary.category_totals(october)
    assert len(october) == 3
    assert totals["Food"] == 400
    assert totals.index[0] == "Food"  # biggest first


def test_monthly_totals():
    assert summary.monthly_totals(_df()).to_dict() == {"2026-09": 1000.0, "2026-10": 600.0}
    assert summary.available_months(_df()) == ["2026-10", "2026-09"]


def test_budget_status():
    october = summary.filter_month(_df(), 2026, 10)
    status = summary.budget_status(october, {"Food": 300, "Rent": 6000}).set_index("category")
    assert status.loc["Food", "remaining"] == -100  # over budget
    assert status.loc["Rent", "spent"] == 0
    assert summary.budget_status(october, {}).empty


def test_ai_context_has_totals_but_no_transactions():
    context = build_context(_df(), {"Food": 300}, today=date(2026, 10, 3))
    assert "₹600" in context  # spent this month
    assert "Food" in context
    assert "Lunch" not in context  # individual descriptions must not be sent to Gemini
    assert build_context(_df().iloc[0:0], {}) == "No expenses have been logged yet."
