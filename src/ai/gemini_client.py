"""Thin wrapper around the google-genai SDK. Only this file talks to Gemini."""

from functools import lru_cache

from google import genai
from google.genai import types

from src import config


class MissingAPIKeyError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    if not config.has_api_key():
        raise MissingAPIKeyError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


def generate(contents, system_instruction: str | None = None, temperature: float = 0.4) -> str:
    """Send text (or a list of chat turns) to Gemini and return the reply as plain text."""
    response = get_client().models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=temperature),
    )
    return response.text or ""


def list_model_names() -> list[str]:
    return [model.name for model in get_client().models.list()]
