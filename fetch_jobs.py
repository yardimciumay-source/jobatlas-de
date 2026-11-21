
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# İlk test için örnek Greenhouse şirket panoları.
# Bunların aktifliği ve Almanya ilanları testte doğrulanacak.
COMPANIES = [
    "contentful",
    "sumup",
    "n26"
]

API_BASE = "https://boards-api.greenhouse.io/v1/boards"

def fetch_company_jobs(company):
    url = f"{API_BASE}/{company}/jobs"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "JobAtlasDE/0.1"}
    )

    try:
        with urllib.request.urlopen(
            request, timeout=20
        ) as response:
            data = json.load(response)

        return data.get("jobs", [])

    except (urllib.error.URLError, ValueError) as error:
        print(f"Fehler bei {company}: {error}")
        return []


def is_germany(job):
    location = job.get("location") or {}
    name = location.get("name", "").lower()

    keywords = [
        "germany", "deutschland",
        "berlin", "munich", "münchen",
        "hamburg", "frankfurt",
        "stuttgart", "köln", "cologne",
        "düsseldorf", "dusseldorf",
        "leipzig", "hannover",
        "remote - germany",
        "remote germany"
    ]

    return any(word in name for word in keywords)


def main():
    all_jobs = []
    seen = set()

    for company in COMPANIES:
        print(f"Lade Stellenangebote: {company}")

        jobs = fetch_company_jobs(company)

        for job in jobs:
            if not is_germany(job):
                continue

            job_id = f"{company}-{job.get('id')}"

            if job_id in seen:
                continue

            seen.add(job_id)

            all_jobs.append({
                "id": job_id,
                "title": job.get("title", ""),
                "company": company,
                "city": (
                    job.get("location") or {}
                ).get("name", ""),
                "language": "unknown",
                "url": job.get("absolute_url", ""),
                "source": "greenhouse"
            })

    output = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "total": len(all_jobs),
        "jobs": all_jobs
    }

    with open(
        "jobs.json", "w", encoding="utf-8"
    ) as file:
        json.dump(
            output, file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Fertig! {len(all_jobs)} Jobs gespeichert.")


if __name__ == "__main__":
    main()
