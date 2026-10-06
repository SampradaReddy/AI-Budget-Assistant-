"""Database connection. One engine for the whole app."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import DATA_DIR, DATABASE_URL

# Streamlit runs each user session in its own thread, and SQLite refuses
# cross-thread use unless we switch that check off.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """All table classes inherit from this."""


def init_db() -> None:
    """Create the tables if they don't exist yet. Safe to call every time the app starts."""
    from src.database import models  # noqa: F401  (import registers the tables on Base)

    DATA_DIR.mkdir(exist_ok=True)
    Base.metadata.create_all(engine)
