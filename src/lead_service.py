"""Lead CRM queries and validation."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from src.database import get_connection

STATUSES = ["new", "contacted", "qualified", "proposal", "won", "lost"]
PRIORITIES = ["low", "medium", "high"]


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def validate_lead(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name", "")).strip()
    company = str(data.get("company", "")).strip()
    email = str(data.get("email", "")).strip()
    status = str(data.get("status", "new")).strip().lower()
    priority = str(data.get("priority", "medium")).strip().lower()
    notes = str(data.get("notes") or "").strip()

    if not name:
        raise ValueError("Name is required.")
    if not company:
        raise ValueError("Company is required.")
    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}.")
    if priority not in PRIORITIES:
        raise ValueError(f"Priority must be one of: {', '.join(PRIORITIES)}.")

    return {
        "name": name,
        "company": company,
        "email": email,
        "status": status,
        "priority": priority,
        "follow_up_date": _as_date(data.get("follow_up_date")),
        "notes": notes,
    }


def list_leads(
    status: str | None = None,
    priority: str | None = None,
    overdue_only: bool = False,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM leads WHERE 1=1"
    params: list[Any] = []

    if status and status != "all":
        query += " AND status = %s"
        params.append(status)
    if priority and priority != "all":
        query += " AND priority = %s"
        params.append(priority)
    if overdue_only:
        query += " AND follow_up_date IS NOT NULL AND follow_up_date < CURRENT_DATE"
        query += " AND status NOT IN ('won', 'lost')"

    query += " ORDER BY follow_up_date NULLS LAST, id"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return list(rows)


def get_lead(lead_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = %s", (lead_id,)).fetchone()
    return row


def create_lead(data: dict[str, Any]) -> dict[str, Any]:
    lead = validate_lead(data)
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO leads (name, company, email, status, priority, follow_up_date, notes)
            VALUES (%(name)s, %(company)s, %(email)s, %(status)s, %(priority)s, %(follow_up_date)s, %(notes)s)
            RETURNING *
            """,
            lead,
        ).fetchone()
    return row


def update_lead(lead_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    if get_lead(lead_id) is None:
        return None
    lead = validate_lead(data)
    lead["id"] = lead_id
    with get_connection() as conn:
        row = conn.execute(
            """
            UPDATE leads
            SET name = %(name)s,
                company = %(company)s,
                email = %(email)s,
                status = %(status)s,
                priority = %(priority)s,
                follow_up_date = %(follow_up_date)s,
                notes = %(notes)s
            WHERE id = %(id)s
            RETURNING *
            """,
            lead,
        ).fetchone()
    return row


def delete_lead(lead_id: int) -> bool:
    with get_connection() as conn:
        result = conn.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    return result.rowcount > 0


def count_leads() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()
    return int(row["total"])


def count_pending_follow_ups() -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM leads
            WHERE follow_up_date IS NOT NULL
              AND follow_up_date <= CURRENT_DATE
              AND status NOT IN ('won', 'lost')
            """
        ).fetchone()
    return int(row["total"])


def find_stale_leads(days: int) -> list[dict[str, Any]]:
    if days < 0:
        raise ValueError("days must be 0 or greater.")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM leads
            WHERE follow_up_date IS NOT NULL
              AND follow_up_date <= CURRENT_DATE - (%s * INTERVAL '1 day')
              AND status NOT IN ('won', 'lost')
            ORDER BY follow_up_date, id
            """,
            (days,),
        ).fetchall()
    return list(rows)


def seed_sample_leads() -> int:
    """Insert fictional leads only if the table is empty."""
    if count_leads() > 0:
        return 0

    today = date.today()
    samples = [
        {
            "name": "Ava Chen",
            "company": "Harbor Analytics",
            "email": "ava.chen@harboranalytics.example",
            "status": "contacted",
            "priority": "high",
            "follow_up_date": today - timedelta(days=5),
            "notes": "Asked for a pilot of Atlas Insights.",
        },
        {
            "name": "Marcus Reid",
            "company": "Northwind Retail",
            "email": "marcus.reid@northwind.example",
            "status": "qualified",
            "priority": "high",
            "follow_up_date": today - timedelta(days=2),
            "notes": "Wants monthly forecasting for 40 stores.",
        },
        {
            "name": "Priya Nair",
            "company": "Lumen Health",
            "email": "priya.nair@lumenhealth.example",
            "status": "proposal",
            "priority": "medium",
            "follow_up_date": today,
            "notes": "Reviewing Team plan pricing.",
        },
        {
            "name": "Jonah Blake",
            "company": "Cedar Logistics",
            "email": "jonah.blake@cedarlogistics.example",
            "status": "new",
            "priority": "medium",
            "follow_up_date": today + timedelta(days=3),
            "notes": "Inbound from website demo form.",
        },
        {
            "name": "Sofia Alvarez",
            "company": "Brightline Media",
            "email": "sofia.alvarez@brightline.example",
            "status": "contacted",
            "priority": "low",
            "follow_up_date": today - timedelta(days=12),
            "notes": "Interested in Pulse Alerts only.",
        },
        {
            "name": "Kenji Sato",
            "company": "Orbit Fintech",
            "email": "kenji.sato@orbitfintech.example",
            "status": "qualified",
            "priority": "high",
            "follow_up_date": today - timedelta(days=1),
            "notes": "Security questionnaire in progress.",
        },
        {
            "name": "Elena Rossi",
            "company": "Vista Foods",
            "email": "elena.rossi@vistafoods.example",
            "status": "new",
            "priority": "low",
            "follow_up_date": today + timedelta(days=7),
            "notes": "Referred by Marcus Reid.",
        },
        {
            "name": "Daniel Okonkwo",
            "company": "Summit Clinics",
            "email": "daniel.okonkwo@summitclinics.example",
            "status": "won",
            "priority": "medium",
            "follow_up_date": today - timedelta(days=20),
            "notes": "Closed Team plan. Check-in next quarter.",
        },
        {
            "name": "Maya Thompson",
            "company": "Riverstone Insurance",
            "email": "maya.thompson@riverstone.example",
            "status": "lost",
            "priority": "low",
            "follow_up_date": today - timedelta(days=30),
            "notes": "Chose an incumbent vendor.",
        },
        {
            "name": "Owen Patel",
            "company": "Cascade Energy",
            "email": "owen.patel@cascadeenergy.example",
            "status": "proposal",
            "priority": "high",
            "follow_up_date": today - timedelta(days=8),
            "notes": "Waiting on legal review of MSA.",
        },
        {
            "name": "Hana Kim",
            "company": "PixelForge Studio",
            "email": "hana.kim@pixelforge.example",
            "status": "contacted",
            "priority": "medium",
            "follow_up_date": today,
            "notes": "Asked for a 15-minute product walkthrough.",
        },
        {
            "name": "Luis Romero",
            "company": "Atlas Manufacturing",
            "email": "luis.romero@atlasmfg.example",
            "status": "new",
            "priority": "high",
            "follow_up_date": today - timedelta(days=4),
            "notes": "Needs on-prem data export option.",
        },
    ]

    created = 0
    for sample in samples:
        create_lead(sample)
        created += 1
    return created
