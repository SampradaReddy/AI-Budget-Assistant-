"""Guess an expense's category from its description.

How it works:
  1. TF-IDF turns each description into numbers (which words/letter-groups appear, and how rare they are).
  2. Logistic regression learns which numbers go with which category.

The model trains on data/training_data.csv. That takes well under a second, so we
just train once when the app starts instead of saving a model file to disk.
"""

from functools import lru_cache

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline

from src.config import DATA_DIR

TRAINING_FILE = DATA_DIR / "training_data.csv"

# Below this confidence the guess isn't trustworthy, so we fall back to "Other".
MIN_CONFIDENCE = 0.25


def train(training_file=TRAINING_FILE) -> Pipeline:
    data = pd.read_csv(training_file)
    model = make_pipeline(
        # char_wb n-grams look at letter groups, so "zomato" still matches "zomatto" or "Zomato*order".
        TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 4)),
        LogisticRegression(max_iter=1000, C=10),
    )
    model.fit(data["description"], data["category"])
    return model


@lru_cache(maxsize=1)
def get_model() -> Pipeline:
    """Train once, then reuse the same model for every call."""
    return train()


def predict(description: str) -> tuple[str, float]:
    """Returns (category, confidence between 0 and 1)."""
    if not description or not description.strip():
        return "Other", 0.0

    model = get_model()
    probabilities = model.predict_proba([description])[0]
    best = probabilities.argmax()
    category, confidence = model.classes_[best], float(probabilities[best])

    if confidence < MIN_CONFIDENCE:
        return "Other", confidence
    return category, confidence


def predict_many(descriptions: list[str]) -> list[str]:
    return [predict(text)[0] for text in descriptions]
