"""Conversation history and simple preference memory."""

from __future__ import annotations

from typing import Any

from src.database import get_connection

DEFAULT_TONE = "professional"
VALID_TONES = ["professional", "friendly", "concise"]


def save_message(role: str, message: str, page: str = "general") -> None:
    text = (message or "").strip()
    if not text:
        return
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (page, role, message)
            VALUES (%s, %s, %s)
            """,
            (page, role, text),
        )


def list_messages(page: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if page:
            rows = conn.execute(
                """
                SELECT * FROM conversations
                WHERE page = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (page, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM conversations
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
    return list(reversed(rows))


def get_preference(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM user_preferences WHERE key = %s",
            (key,),
        ).fetchone()
    return row["value"] if row else default


def set_preference(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_preferences (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, value.strip()),
        )


def get_email_tone() -> str:
    tone = get_preference("email_tone", DEFAULT_TONE).lower()
    return tone if tone in VALID_TONES else DEFAULT_TONE


def set_email_tone(tone: str) -> str:
    cleaned = tone.strip().lower()
    if cleaned not in VALID_TONES:
        raise ValueError(f"Email tone must be one of: {', '.join(VALID_TONES)}.")
    set_preference("email_tone", cleaned)
    return cleaned


def recent_context(page: str, limit: int = 8) -> list[dict[str, str]]:
    """Return recent chat messages in OpenAI message format."""
    rows = list_messages(page=page, limit=limit)
    return [{"role": row["role"], "content": row["message"]} for row in rows]
