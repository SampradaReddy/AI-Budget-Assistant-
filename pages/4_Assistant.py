"""Chat with Gemini about your spending."""

import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

from src import config
from src.ai import assistant
from src.database import crud
from src.database.db import init_db

st.set_page_config(page_title="Assistant", page_icon="🤖")
init_db()

st.title("🤖 Budget Assistant")

if not config.has_api_key():
    st.warning("Add your Gemini API key to use the assistant.")
    st.markdown(
        "1. Get a key from [Google AI Studio](https://aistudio.google.com/apikey)\n"
        "2. Copy `.env.example` to `.env`\n"
        "3. Paste the key after `GEMINI_API_KEY=`\n"
        "4. Stop the app (Ctrl+C) and run `streamlit run app.py` again"
    )
    st.stop()

# Chat history lives in st.session_state, so it survives reruns but resets on browser refresh.
history = StreamlitChatMessageHistory(key="chat_messages")
context = assistant.build_context(crud.get_expenses_df(), crud.get_budgets())

with st.sidebar:
    st.caption(f"Model: `{config.GEMINI_MODEL}`")
    with st.expander("What the assistant can see"):
        st.text(context)
    if st.button("Clear chat"):
        history.clear()
        st.rerun()

if not history.messages:
    st.caption("Try: *Where am I overspending?* · *How much can I spend per day for the rest of the month?*")

for message in history.messages:
    st.chat_message("user" if message.type == "human" else "assistant").write(message.content)

if question := st.chat_input("Ask about your budget"):
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = assistant.ask(question, context, history.messages)
            st.write(answer)
            history.add_user_message(question)
            history.add_ai_message(answer)
        except Exception as error:
            st.error(
                f"Gemini request failed: {error}\n\n"
                "If this is a model-not-found error, run `python -m scripts.list_models` "
                "and set GEMINI_MODEL in `.env` to one of the names it prints."
            )
