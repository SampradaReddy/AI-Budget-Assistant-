"""All reads and writes go through these functions, so pages never touch SQL directly."""

from datetime import date

import pandas as pd
from sqlalchemy import delete, select

from src.database.db import SessionLocal, engine
from src.database.models import Budget, Expense

EXPENSE_COLUMNS = ["id", "date", "description", "amount", "category"]


# ---------- Expenses ----------

def add_expense(day: date, description: str, amount: float, category: str) -> Expense:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if not description.strip():
        raise ValueError("Description cannot be empty.")

    expense = Expense(date=day, description=description.strip(), amount=float(amount), category=category)
    with SessionLocal() as session:
        session.add(expense)
        session.commit()
    return expense


def add_expenses_bulk(rows: list[dict]) -> int:
    """rows: [{"date": date, "description": str, "amount": float, "category": str}, ...]"""
    with SessionLocal() as session:
        session.add_all([Expense(**row) for row in rows])
        session.commit()
    return len(rows)


def delete_expense(expense_id: int) -> None:
    with SessionLocal() as session:
        session.execute(delete(Expense).where(Expense.id == expense_id))
        session.commit()


def get_expenses_df() -> pd.DataFrame:
    """Every expense as a DataFrame, newest first. `date` is a pandas datetime column."""
    query = select(Expense.id, Expense.date, Expense.description, Expense.amount, Expense.category)
    df = pd.read_sql(query, engine)
    if df.empty:
        return pd.DataFrame(columns=EXPENSE_COLUMNS).astype({"amount": float})
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["date", "id"], ascending=False).reset_index(drop=True)


# ---------- Budgets ----------

def set_budget(category: str, monthly_limit: float) -> None:
    """Create or update the limit for a category. A limit of 0 removes it."""
    with SessionLocal() as session:
        budget = session.scalar(select(Budget).where(Budget.category == category))
        if monthly_limit <= 0:
            if budget:
                session.delete(budget)
        elif budget:
            budget.monthly_limit = float(monthly_limit)
        else:
            session.add(Budget(category=category, monthly_limit=float(monthly_limit)))
        session.commit()


def get_budgets() -> dict[str, float]:
    """{"Food": 5000.0, ...}"""
    with SessionLocal() as session:
        return {b.category: b.monthly_limit for b in session.scalars(select(Budget))}
