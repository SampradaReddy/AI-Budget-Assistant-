from datetime import date

import pytest

from src.database import crud


def test_add_and_read_expense():
    crud.add_expense(date(2026, 10, 1), "Swiggy order", 250, "Food")
    df = crud.get_expenses_df()
    assert len(df) == 1
    assert df.loc[0, "amount"] == 250
    assert df.loc[0, "category"] == "Food"


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        crud.add_expense(date(2026, 10, 1), "Free lunch", 0, "Food")
    with pytest.raises(ValueError):
        crud.add_expense(date(2026, 10, 1), "   ", 100, "Food")


def test_delete_expense():
    expense = crud.add_expense(date(2026, 10, 1), "Uber ride", 180, "Transport")
    crud.delete_expense(expense.id)
    assert crud.get_expenses_df().empty


def test_budget_create_update_remove():
    crud.set_budget("Food", 5000)
    assert crud.get_budgets() == {"Food": 5000.0}
    crud.set_budget("Food", 4000)
    assert crud.get_budgets() == {"Food": 4000.0}
    crud.set_budget("Food", 0)
    assert crud.get_budgets() == {}
