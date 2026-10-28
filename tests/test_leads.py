import pytest

from src.lead_service import validate_lead


def test_validate_lead_accepts_complete_data():
    lead = validate_lead(
        {
            "name": "Ava Chen",
            "company": "Harbor Analytics",
            "email": "ava@example.com",
            "status": "new",
            "priority": "high",
            "follow_up_date": "2026-10-28",
            "notes": "Pilot request",
        }
    )
    assert lead["name"] == "Ava Chen"
    assert lead["status"] == "new"


def test_validate_lead_rejects_missing_email():
    with pytest.raises(ValueError, match="email"):
        validate_lead(
            {
                "name": "Ava Chen",
                "company": "Harbor Analytics",
                "email": "not-an-email",
                "status": "new",
                "priority": "medium",
            }
        )


def test_validate_lead_rejects_unknown_status():
    with pytest.raises(ValueError, match="Status"):
        validate_lead(
            {
                "name": "Ava Chen",
                "company": "Harbor Analytics",
                "email": "ava@example.com",
                "status": "hot-lead",
                "priority": "medium",
            }
        )
