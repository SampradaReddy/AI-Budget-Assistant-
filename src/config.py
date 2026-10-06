"""Central settings. Everything that might change lives here, not scattered in the code."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# Reads .env into environment variables (does nothing if the file is missing).
load_dotenv(ROOT_DIR / ".env")

# SQLite file by default. Point this at Postgres later and nothing else has to change.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'budget.db').as_posix()}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

CURRENCY = os.getenv("CURRENCY_SYMBOL", "₹")

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Rent",
    "Other",
]


def has_api_key() -> bool:
    """True only if a real key is set (not empty, not the placeholder)."""
    return bool(GEMINI_API_KEY) and GEMINI_API_KEY != "your_key_here"


def money(amount: float) -> str:
    """Format a number as currency, e.g. 4500 -> ₹4,500 and -300 -> -₹300."""
    sign = "-" if amount < 0 else ""
    return f"{sign}{CURRENCY}{abs(amount):,.0f}"
