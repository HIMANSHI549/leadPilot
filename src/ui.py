"""Shared Streamlit helpers."""

from __future__ import annotations

import streamlit as st

from src.database import init_db
from src.lead_service import seed_sample_leads


def bootstrap() -> None:
    st.set_page_config(page_title="LeadPilot AI", layout="wide")
    try:
        init_db()
        seed_sample_leads()
    except Exception as exc:
        st.error(
            "Could not connect to PostgreSQL. Check DATABASE_URL in `.env` "
            "and make sure pgvector is enabled."
        )
        st.exception(exc)
        st.stop()
