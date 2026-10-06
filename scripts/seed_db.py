"""Fill the database with sample data.  Run:  python -m scripts.seed_db"""

from src import sample_data
from src.database.db import init_db

if __name__ == "__main__":
    init_db()
    print(f"Added {sample_data.load()} sample expenses and default budgets.")
