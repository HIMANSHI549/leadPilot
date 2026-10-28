"""Create the fictional product PDF used by the RAG page."""

from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "sample_company_profile.pdf"

PARAGRAPHS = [
    "Atlas Insights — Company Product Guide (fictional)",
    "Company: Atlas Insights is a fictional analytics company used by LeadPilot AI for training demos. Headquarters: Seattle, Washington. Founded: 2021. Employees: 85.",
    "Product: The core product is Atlas Insights Cloud, a dashboard that helps mid-size companies forecast demand, watch sales pipeline health, and send Pulse Alerts when a metric changes by more than 8 percent in a single day.",
    "Plans and pricing: Starter is $49 per user each month and includes 3 dashboards and email alerts. Team is $99 per user each month and includes 20 dashboards, Pulse Alerts, and CSV export. Scale is $179 per user each month and includes API access, SSO, and a dedicated analyst.",
    "Pilot program: New customers can run a 14-day pilot. The pilot includes one dashboard, one data source, and a weekly check-in with a customer success manager. Pilots do not include SSO.",
    "Support: Support hours are Monday through Friday, 8:00 to 18:00 Pacific Time. Starter customers receive email support. Team and Scale customers receive chat support. Scale customers also receive a named success manager.",
    "Security: Atlas Insights encrypts data in transit with TLS 1.2 or later. Data at rest is encrypted with AES-256. The company completes a SOC 2 Type II review each year in this fictional story. Customer data is stored in the United States unless a Scale customer requests EU hosting.",
    "Common objections: On-premises deployment is not available on Starter or Team. Scale customers may export nightly snapshots to their own object storage. Native Salesforce sync is on the Team and Scale plans only. Phone support is not included on any plan.",
    "Glossary: Pulse Alerts are automatic notifications when a tracked KPI moves beyond a threshold. Atlas Forecast is a 13-week demand forecast built from the last 24 months of sales history.",
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    page = document.new_page()
    y = 72
    for paragraph in PARAGRAPHS:
        if y > 720:
            page = document.new_page()
            y = 72
        rect = fitz.Rect(72, y, 540, y + 110)
        overflow = page.insert_textbox(rect, paragraph, fontsize=11, fontname="helv")
        y += 110 - overflow
    document.save(OUTPUT)
    document.close()
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
