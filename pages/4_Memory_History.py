import streamlit as st

from src.llm_service import LLMError, generate_response
from src.memory_service import (
    VALID_TONES,
    get_email_tone,
    list_messages,
    recent_context,
    save_message,
    set_email_tone,
)
from src.ui import bootstrap

bootstrap()

st.title("Memory and History")
st.caption("Conversations and a simple email-tone preference are stored in PostgreSQL.")

st.subheader("Email tone preference")
current_tone = get_email_tone()
tone = st.selectbox("Preferred email tone", VALID_TONES, index=VALID_TONES.index(current_tone))
if st.button("Save preference"):
    set_email_tone(tone)
    st.success(f"Saved email tone: {tone}. New drafts will use this setting.")

st.subheader("Chat that uses saved memory")
st.write("This chat loads recent history and includes your preferred email tone in the prompt.")

if "memory_messages" not in st.session_state:
    st.session_state.memory_messages = recent_context("memory", limit=10)

for message in st.session_state.memory_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask something, or describe how you like emails written")
if prompt is not None:
    if not prompt.strip():
        st.warning("Please enter a non-empty message.")
    else:
        st.session_state.memory_messages.append({"role": "user", "content": prompt})
        save_message("user", prompt, page="memory")
        with st.chat_message("user"):
            st.markdown(prompt)

        tone = get_email_tone()
        history = [
            {
                "role": "user",
                "content": (
                    f"The user's saved email tone preference is: {tone}. "
                    "If they state a new preference, acknowledge it and remind them to save it "
                    "with the selector above if they want it stored."
                ),
            },
            *st.session_state.memory_messages,
        ]
        with st.chat_message("assistant"):
            with st.spinner("Generating a reply with saved context..."):
                try:
                    message = generate_response(history)
                    answer = (message.content or "").strip()
                    st.markdown(answer)
                except LLMError as exc:
                    answer = str(exc)
                    st.error(answer)

        st.session_state.memory_messages.append({"role": "assistant", "content": answer})
        save_message("assistant", answer, page="memory")

st.subheader("Recent saved conversations")
history_rows = list_messages(limit=30)
if not history_rows:
    st.info("No saved messages yet.")
else:
    st.dataframe(
        [
            {
                "when": row["created_at"],
                "page": row["page"],
                "role": row["role"],
                "message": row["message"],
            }
            for row in reversed(history_rows)
        ],
        use_container_width=True,
        hide_index=True,
    )
