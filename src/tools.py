"""Predefined Python tools the LLM can request. The model never runs SQL itself."""

from __future__ import annotations

import json
from typing import Any, Callable

from src.lead_service import find_stale_leads as query_stale_leads
from src.lead_service import get_lead
from src.memory_service import get_email_tone

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "find_stale_leads",
            "description": "Find leads whose follow-up date is at least this many days overdue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "How many days overdue. Use 0 for anything due today or earlier.",
                    }
                },
                "required": ["days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lead_details",
            "description": "Look up one lead by numeric ID and return its stored details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "integer",
                        "description": "The lead ID from the dashboard.",
                    }
                },
                "required": ["lead_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_followup_email",
            "description": "Draft a follow-up email using the lead's real details and saved email tone. Does not send email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "integer",
                        "description": "The lead ID to write to.",
                    }
                },
                "required": ["lead_id"],
            },
        },
    },
]


def _parse_arguments(raw_arguments: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("The model supplied invalid JSON arguments.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    return parsed


def _require_int(arguments: dict[str, Any], name: str) -> int:
    if name not in arguments:
        raise ValueError(f"Missing required argument: {name}")
    try:
        value = int(arguments[name])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    return value


def find_stale_leads(days: int) -> str:
    leads = query_stale_leads(days)
    if not leads:
        return json.dumps({"count": 0, "leads": [], "message": f"No leads are {days} or more days overdue."})
    payload = [
        {
            "id": lead["id"],
            "name": lead["name"],
            "company": lead["company"],
            "email": lead["email"],
            "status": lead["status"],
            "priority": lead["priority"],
            "follow_up_date": str(lead["follow_up_date"]),
        }
        for lead in leads
    ]
    return json.dumps({"count": len(payload), "leads": payload})


def get_lead_details(lead_id: int) -> str:
    lead = get_lead(lead_id)
    if lead is None:
        return json.dumps({"error": f"No lead found with id {lead_id}."})
    return json.dumps(
        {
            "id": lead["id"],
            "name": lead["name"],
            "company": lead["company"],
            "email": lead["email"],
            "status": lead["status"],
            "priority": lead["priority"],
            "follow_up_date": str(lead["follow_up_date"]) if lead["follow_up_date"] else None,
            "notes": lead["notes"],
        }
    )


def draft_followup_email(lead_id: int) -> str:
    lead = get_lead(lead_id)
    if lead is None:
        return json.dumps({"error": f"No lead found with id {lead_id}."})
    tone = get_email_tone()
    return json.dumps(
        {
            "lead_id": lead["id"],
            "recipient_name": lead["name"],
            "recipient_email": lead["email"],
            "company": lead["company"],
            "status": lead["status"],
            "priority": lead["priority"],
            "follow_up_date": str(lead["follow_up_date"]) if lead["follow_up_date"] else None,
            "notes": lead["notes"],
            "email_tone": tone,
            "instruction": (
                "Draft a follow-up email only. Do not send it. "
                f"Write in a {tone} tone. Use the lead's real name, company, and notes. "
                "Ask the user to confirm before any real email would be sent."
            ),
        }
    )


HANDLERS: dict[str, Callable[..., str]] = {
    "find_stale_leads": find_stale_leads,
    "get_lead_details": get_lead_details,
    "draft_followup_email": draft_followup_email,
}


def execute_tool(name: str, raw_arguments: str | dict[str, Any]) -> str:
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        arguments = _parse_arguments(raw_arguments)
        if name == "find_stale_leads":
            days = _require_int(arguments, "days")
            if days < 0:
                raise ValueError("days must be 0 or greater.")
            return handler(days)
        if name in {"get_lead_details", "draft_followup_email"}:
            lead_id = _require_int(arguments, "lead_id")
            if lead_id <= 0:
                raise ValueError("lead_id must be a positive integer.")
            return handler(lead_id)
        return json.dumps({"error": f"Tool {name} is not implemented."})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        return json.dumps({"error": f"Tool {name} failed: {exc}"})
