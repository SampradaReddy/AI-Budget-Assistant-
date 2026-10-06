"""The chat assistant, built as a small LangChain pipeline:

    prompt template  ->  Gemini  ->  text

Design rule: Python does the maths, Gemini does the talking. We compute the
numbers with pandas, hand Gemini a short summary, and ask it to explain. Gemini
never sees individual transactions, only totals.
"""

from datetime import date

import pandas as pd
from google.genai import types
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda

from src.ai import gemini_client
from src.analytics import summary
from src.config import money
from src.ml.forecaster import forecast_month_end

SYSTEM_PROMPT = """You are a friendly personal budget assistant for a student in India.

Rules:
- Use ONLY the numbers in the summary below. Never invent figures.
- If the summary doesn't contain what you need, say so and suggest what to log.
- Be specific and practical. Keep answers short (under 150 words unless asked for more).
- You give general budgeting guidance, not professional financial advice.

User's financial summary:
{context}"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def build_context(df: pd.DataFrame, budgets: dict[str, float], today: date | None = None) -> str:
    """Turn the user's data into a short text summary for the prompt (totals only)."""
    today = today or date.today()
    if df.empty:
        return "No expenses have been logged yet."

    month_df = summary.current_month(df, today)
    forecast = forecast_month_end(df, today)
    lines = [
        f"Today: {today:%d %B %Y} (day {forecast['days_elapsed']} of {forecast['days_in_month']})",
        f"Spent this month: {money(forecast['spent_so_far'])}",
        f"Projected month-end total: {money(forecast['projected_total'])}",
    ]

    totals = summary.category_totals(month_df)
    if not totals.empty:
        lines.append("This month by category: " + ", ".join(f"{c} {money(a)}" for c, a in totals.items()))

    status = summary.budget_status(month_df, budgets)
    if status.empty:
        lines.append("No budgets set.")
    else:
        lines.append(f"Total monthly budget: {money(status['limit'].sum())}")
        lines.append(
            "Budgets (spent / limit): "
            + ", ".join(f"{r.category} {money(r.spent)} / {money(r.limit)}" for r in status.itertuples())
        )

    monthly = summary.monthly_totals(df).tail(4)
    if len(monthly) > 1:
        lines.append("Recent monthly totals: " + ", ".join(f"{m} {money(a)}" for m, a in monthly.items()))

    return "\n".join(lines)


def _call_gemini(prompt_value: PromptValue) -> str:
    """Convert LangChain messages into the format google-genai expects, then call Gemini."""
    system_text = None
    contents = []
    for message in prompt_value.to_messages():
        if isinstance(message, SystemMessage):
            system_text = message.content
        else:
            contents.append(types.Content(role=_role(message), parts=[types.Part(text=str(message.content))]))
    return gemini_client.generate(contents, system_instruction=system_text)


def _role(message: BaseMessage) -> str:
    # Gemini calls the assistant's turns "model" instead of "assistant".
    return "model" if isinstance(message, AIMessage) else "user"


def build_chain() -> Runnable:
    return prompt | RunnableLambda(_call_gemini)


def ask(question: str, context: str, history: list[BaseMessage] | None = None) -> str:
    return build_chain().invoke({"question": question, "context": context, "history": history or []})
