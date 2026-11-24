import requests
from datetime import datetime, timedelta, timezone

# 1. Look back 24 hours for newly declared residential disasters
yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")

base_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
params = {
    "$filter": (
        f"ihProgramDeclared eq true and "
        f"declarationDate ge '{yesterday}' and "
        f"(incidentType eq 'Fire' or incidentType eq 'Tornado' or "
        f"incidentType eq 'Hurricane' or incidentType eq 'Flood')"
    ),
    "$orderby": "declarationDate desc",
    "$select": "disasterNumber,state,designatedArea,incidentType,declarationTitle,declarationDate,fipsStateCode,fipsCountyCode,hmProgramDeclared"
}

def fetch_rebuild_leads():
    response = requests.get(base_url, params=params, timeout=15)
    response.raise_for_status()
    records = response.json().get("DisasterDeclarationsSummaries", [])

    if not records:
        print("No new total-loss residential disasters declared in the last 24 hours.")
        return

    print(f"Found {len(records)} high-priority target counties:\n")
    for r in records:
        fips = f"{r['fipsStateCode']}{r['fipsCountyCode']}"
        mitigation = "YES (Pitch Fortified/Elevated Plans)" if r.get("hmProgramDeclared") else "No"
        print(
            f"[{r['state']}] {r['designatedArea']} (FIPS: {fips}) | "
            f"Event: {r['incidentType']} - {r['declarationTitle']} | "
            f"Hazard Mitigation Active: {mitigation}"
        )

if __name__ == "__main__":
    fetch_rebuild_leads()
