"""Point the app at a throwaway database BEFORE any src module is imported,
so tests never touch your real data/budget.db."""

import os
import tempfile
from pathlib import Path

_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_tmp_dir) / 'test.db').as_posix()}"

import pytest  # noqa: E402

from src.database.db import Base, engine, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    """Every test starts with empty tables."""
    init_db()
    yield
    Base.metadata.drop_all(engine)
