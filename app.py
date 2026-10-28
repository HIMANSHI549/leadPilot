import streamlit as st

from src.config import missing_config
from src.ui import bootstrap

bootstrap()

st.title("LeadPilot AI")
st.caption("A beginner-friendly mini CRM with document Q&A, tool calling, and simple memory.")

st.markdown(
    """
Use the sidebar to open one of the four pages:

1. **Lead Dashboard** — add, edit, filter, and delete sales leads.
2. **Document Chat** — upload a PDF, retrieve relevant chunks, and ask grounded questions.
3. **AI Sales Assistant** — let the model call Python tools for overdue leads and email drafts.
4. **Memory and History** — save conversation history and an email-tone preference.
    """
)

st.info(
    "This first version is a single local user. Secrets stay in `.env` and are never written to Git."
)

needed = missing_config()
if needed:
    st.warning(
        "Add these values in `.env` before using AI features: " + ", ".join(needed)
    )

with st.sidebar:
    st.header("LeadPilot AI")
    st.write("Python · Streamlit · PostgreSQL · pgvector · LLM APIs")
    st.page_link("pages/1_Lead_Dashboard.py", label="Lead Dashboard")
    st.page_link("pages/2_Document_Chat.py", label="Chat with Documents")
    st.page_link("pages/3_AI_Sales_Assistant.py", label="AI Sales Assistant")
    st.page_link("pages/4_Memory_History.py", label="Memory and History")
