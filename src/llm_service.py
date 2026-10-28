"""Thin wrapper around an OpenAI-compatible chat and embedding API."""

from __future__ import annotations

from typing import Any, Callable

from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from src.config import EMBEDDING_MODEL, OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = (
    "You are LeadPilot AI, a careful sales assistant. "
    "Use only the information you are given. If you do not know something, say so. "
    "Never claim that you sent a real email. Ask for confirmation before any real-world action."
)


class LLMError(Exception):
    """User-facing error for chat and embedding calls."""


def get_client() -> OpenAI:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_api_key_here":
        raise LLMError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add your API key."
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_response(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    model: str | None = None,
) -> Any:
    """Send a chat completion request. Returns the first choice message."""
    if not messages:
        raise LLMError("There is no message to send.")

    last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if last_user and not str(last_user.get("content") or "").strip():
        raise LLMError("Please enter a non-empty question.")

    payload: dict[str, Any] = {
        "model": model or OPENAI_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "temperature": 0.3,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = get_client().chat.completions.create(**payload)
    except RateLimitError as exc:
        raise LLMError("The LLM API rate limit was reached. Wait a moment and try again.") from exc
    except APITimeoutError as exc:
        raise LLMError("The LLM API timed out. Try again with a shorter question.") from exc
    except APIError as exc:
        raise LLMError(f"The LLM API returned an error: {exc}") from exc
    except Exception as exc:
        raise LLMError(f"Could not reach the LLM API: {exc}") from exc

    if not response.choices:
        raise LLMError("The LLM API returned an empty response.")
    return response.choices[0].message


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [text.strip() for text in texts if text and text.strip()]
    if not cleaned:
        raise LLMError("There is no text to embed.")

    try:
        response = get_client().embeddings.create(model=EMBEDDING_MODEL, input=cleaned)
    except RateLimitError as exc:
        raise LLMError("Embedding rate limit reached. Try a smaller document.") from exc
    except APIError as exc:
        raise LLMError(f"Embedding API error: {exc}") from exc
    except Exception as exc:
        raise LLMError(f"Could not create embeddings: {exc}") from exc

    return [item.embedding for item in sorted(response.data, key=lambda row: row.index)]


def run_tool_loop(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    execute_tool: Callable[[str, dict[str, Any]], str],
    max_rounds: int = 4,
) -> str:
    """Let the model pick tools, execute them in Python, then return a final answer."""
    working = list(messages)

    for _ in range(max_rounds):
        message = generate_response(working, tools=tools)
        tool_calls = message.tool_calls or []

        if not tool_calls:
            return (message.content or "").strip() or "I did not produce a response."

        working.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        for call in tool_calls:
            result = execute_tool(call.function.name, call.function.arguments)
            working.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    return "I reached the tool-call limit. Please ask a more specific question."
