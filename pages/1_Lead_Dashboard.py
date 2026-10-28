from datetime import date

import streamlit as st

from src.lead_service import (
    PRIORITIES,
    STATUSES,
    count_leads,
    count_pending_follow_ups,
    create_lead,
    delete_lead,
    list_leads,
    update_lead,
)
from src.ui import bootstrap

bootstrap()

st.title("Lead Dashboard")
st.caption("Create, edit, filter, and delete sales leads stored in PostgreSQL.")

total = count_leads()
pending = count_pending_follow_ups()
col_a, col_b = st.columns(2)
col_a.metric("Total leads", total)
col_b.metric("Pending follow-ups", pending)

st.subheader("Filters")
filter_cols = st.columns(3)
status_filter = filter_cols[0].selectbox("Status", ["all", *STATUSES])
priority_filter = filter_cols[1].selectbox("Priority", ["all", *PRIORITIES])
overdue_only = filter_cols[2].checkbox("Overdue only")

leads = list_leads(
    status=status_filter,
    priority=priority_filter,
    overdue_only=overdue_only,
)

st.subheader("Leads")
if not leads:
    st.warning("No leads match these filters.")
else:
    display_rows = [
        {
            "id": lead["id"],
            "name": lead["name"],
            "company": lead["company"],
            "email": lead["email"],
            "status": lead["status"],
            "priority": lead["priority"],
            "follow_up_date": lead["follow_up_date"],
            "notes": lead["notes"],
        }
        for lead in leads
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)

st.subheader("Add a lead")
with st.form("create_lead"):
    name = st.text_input("Name")
    company = st.text_input("Company")
    email = st.text_input("Email")
    status = st.selectbox("Status", STATUSES)
    priority = st.selectbox("Priority", PRIORITIES, index=1)
    follow_up_date = st.date_input("Next follow-up date", value=date.today())
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Save lead")
    if submitted:
        try:
            created = create_lead(
                {
                    "name": name,
                    "company": company,
                    "email": email,
                    "status": status,
                    "priority": priority,
                    "follow_up_date": follow_up_date,
                    "notes": notes,
                }
            )
            st.success(f"Saved lead #{created['id']} — {created['name']}.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

st.subheader("Edit or delete")
if leads:
    selected_id = st.selectbox(
        "Choose a lead",
        options=[lead["id"] for lead in leads],
        format_func=lambda lead_id: next(
            f"#{lead['id']} {lead['name']} ({lead['company']})"
            for lead in leads
            if lead["id"] == lead_id
        ),
    )
    selected = next(lead for lead in leads if lead["id"] == selected_id)
    with st.form("edit_lead"):
        name = st.text_input("Name", value=selected["name"])
        company = st.text_input("Company", value=selected["company"])
        email = st.text_input("Email", value=selected["email"])
        status = st.selectbox("Status", STATUSES, index=STATUSES.index(selected["status"]))
        priority = st.selectbox(
            "Priority", PRIORITIES, index=PRIORITIES.index(selected["priority"])
        )
        follow_up_date = st.date_input(
            "Next follow-up date",
            value=selected["follow_up_date"] or date.today(),
        )
        notes = st.text_area("Notes", value=selected["notes"] or "")
        save = st.form_submit_button("Update lead")
        if save:
            try:
                update_lead(
                    selected_id,
                    {
                        "name": name,
                        "company": company,
                        "email": email,
                        "status": status,
                        "priority": priority,
                        "follow_up_date": follow_up_date,
                        "notes": notes,
                    },
                )
                st.success("Lead updated.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    if st.button("Delete this lead", type="primary"):
        delete_lead(selected_id)
        st.success("Lead deleted.")
        st.rerun()
