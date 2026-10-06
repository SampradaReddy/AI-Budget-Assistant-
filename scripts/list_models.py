"""Show the Gemini models your API key can use.  Run:  python -m scripts.list_models

Pick one and set it as GEMINI_MODEL in .env.
"""

from src.ai.gemini_client import MissingAPIKeyError, list_model_names

if __name__ == "__main__":
    try:
        for name in list_model_names():
            print(name)
    except MissingAPIKeyError as error:
        print(error)
