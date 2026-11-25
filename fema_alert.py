import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import requests

base_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"


def send_alert_email(subject: str, body: str) -> None:
    gmail_user = os.environ["GMAIL_USER"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    alert_recipient = os.environ["ALERT_RECIPIENT"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = alert_recipient
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_app_password)
        smtp.send_message(msg)


def fetch_rebuild_leads(lookback_days: int = 1) -> None:
    yesterday = (
        datetime.now(timezone.utc) - timedelta(days=lookback_days)
    ).strftime("%Y-%m-%dT00:00:00.000Z")

    params = {
        "$filter": (
            f"ihProgramDeclared eq true and "
            f"declarationDate ge '{yesterday}' and "
            f"(incidentType eq 'Fire' or incidentType eq 'Tornado' or "
            f"incidentType eq 'Hurricane' or incidentType eq 'Flood')"
        ),
        "$orderby": "declarationDate desc",
        "$select": (
            "disasterNumber,state,designatedArea,incidentType,"
            "declarationTitle,declarationDate,fipsStateCode,fipsCountyCode,"
            "hmProgramDeclared"
        ),
    }

    response = requests.get(base_url, params=params, timeout=15)
    response.raise_for_status()
    records = response.json().get("DisasterDeclarationsSummaries", [])

    if not records:
        print(
            f"No new total-loss residential disasters declared in the last {lookback_days} day(s)."
        )
        return

    lines = [f"Found {len(records)} high-priority target counties:\n"]
    for r in records:
        fips = f"{r.get('fipsStateCode', '')}{r.get('fipsCountyCode', '')}"
        mitigation = (
            "YES (Pitch Fortified/Elevated Plans)"
            if r.get("hmProgramDeclared")
            else "No"
        )
        line = (
            f"[{r.get('state')}] {r.get('designatedArea')} (FIPS: {fips}) | "
            f"Event: {r.get('incidentType')} - {r.get('declarationTitle')} | "
            f"Hazard Mitigation Active: {mitigation}"
        )
        lines.append(line)

    report = "\n".join(lines)
    print(report)
    send_alert_email(
        subject=f"FEMA Disaster Alert: {len(records)} New Target Area(s)",
        body=report,
    )
    print("Alert email sent.")


if __name__ == "__main__":
    fetch_rebuild_leads(lookback_days=1)
