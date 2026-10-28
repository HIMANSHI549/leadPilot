"""Load environment variables used across the app."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DATABASE_URL = os.getenv("DATABASE_URL", "")
EMBEDDING_DIMENSIONS = 1536


def missing_config() -> list[str]:
    missing = []
    if not DATABASE_URL or "your_postgresql" in DATABASE_URL:
        missing.append("DATABASE_URL")
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_api_key_here":
        missing.append("OPENAI_API_KEY")
    return missing
