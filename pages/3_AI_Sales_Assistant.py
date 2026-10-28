import streamlit as st

from src.llm_service import LLMError, run_tool_loop
from src.memory_service import get_email_tone, recent_context, save_message
from src.tools import TOOL_SCHEMAS, execute_tool
from src.ui import bootstrap

bootstrap()

st.title("AI Sales Assistant")
st.caption(
    "The model can choose Python tools. Your code validates arguments, queries PostgreSQL, "
    "and returns results. Nothing is emailed automatically."
)

st.info(f"Saved email tone: **{get_email_tone()}**. Change it on the Memory and History page.")

st.markdown(
    """
Try questions like:

- Which leads are more than 3 days overdue?
- Summarize lead 2.
- Draft a follow-up email for lead 6.
    """
)

if "assistant_messages" not in st.session_state:
    st.session_state.assistant_messages = recent_context("assistant", limit=8)

for message in st.session_state.assistant_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask the sales assistant")
if prompt is not None:
    if not prompt.strip():
        st.warning("Please enter a non-empty question.")
    else:
        st.session_state.assistant_messages.append({"role": "user", "content": prompt})
        save_message("user", prompt, page="assistant")
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Choosing tools and writing a reply..."):
                try:
                    answer = run_tool_loop(
                        st.session_state.assistant_messages,
                        TOOL_SCHEMAS,
                        execute_tool,
                    )
                except LLMError as exc:
                    answer = str(exc)
                    st.error(answer)
                else:
                    st.markdown(answer)

        st.session_state.assistant_messages.append({"role": "assistant", "content": answer})
        save_message("assistant", answer, page="assistant")
