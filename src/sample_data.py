"""Fake expenses so the app has something to show before you log your own."""

import random
from datetime import date, timedelta

from src.database import crud

# (category, description, min amount, max amount)
EVERYDAY = [
    ("Food", "Lunch at college canteen", 60, 120),
    ("Food", "Swiggy order", 180, 420),
    ("Food", "Chai and snacks", 20, 60),
    ("Food", "Groceries from DMart", 300, 900),
    ("Transport", "Metro card recharge", 100, 300),
    ("Transport", "Rapido bike taxi", 40, 110),
    ("Transport", "Uber ride", 120, 350),
    ("Shopping", "Amazon order", 250, 1500),
    ("Shopping", "Stationery", 50, 200),
    ("Entertainment", "Movie tickets BookMyShow", 200, 500),
    ("Health", "Pharmacy medicines", 80, 400),
    ("Education", "Xerox and printouts", 20, 150),
    ("Other", "Haircut at salon", 150, 400),
]
# Food and transport happen far more often than the rest.
WEIGHTS = [8, 4, 6, 2, 2, 4, 2, 1, 1, 1, 1, 2, 0.5]

MONTHLY = [
    (1, "Rent", "Hostel rent monthly", 6000),
    (3, "Bills", "Jio mobile recharge", 299),
    (5, "Entertainment", "Spotify premium", 119),
    (7, "Bills", "WiFi broadband", 500),
]

DEFAULT_BUDGETS = {
    "Food": 5000,
    "Transport": 2000,
    "Shopping": 2000,
    "Bills": 1000,
    "Entertainment": 1000,
    "Rent": 6000,
}


def generate(days: int = 90, seed: int = 42, today: date | None = None) -> list[dict]:
    rng = random.Random(seed)
    today = today or date.today()
    rows = []
    for offset in range(days, -1, -1):
        day = today - timedelta(days=offset)
        for day_of_month, category, description, amount in MONTHLY:
            if day.day == day_of_month:
                rows.append({"date": day, "description": description, "amount": float(amount), "category": category})
        for category, description, low, high in rng.choices(EVERYDAY, weights=WEIGHTS, k=rng.randint(0, 3)):
            rows.append(
                {"date": day, "description": description, "amount": float(rng.randint(low, high)), "category": category}
            )
    return rows


def load(days: int = 90) -> int:
    """Insert sample expenses and default budgets. Returns how many expenses were added."""
    count = crud.add_expenses_bulk(generate(days))
    for category, limit in DEFAULT_BUDGETS.items():
        crud.set_budget(category, limit)
    return count
