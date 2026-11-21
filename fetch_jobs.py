
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Mevcut çalışan şirketler
GREENHOUSE_COMPANIES = [
    "contentful",
    "sumup",
    "n26"
]

# Arbeitnow'dan ilk 5 sayfayı kontrol edeceğiz
ARBEITNOW_PAGES = 5

GERMAN_LOCATIONS = [
    "germany", "deutschland", "berlin",
    "hamburg", "munich", "münchen",
    "frankfurt", "stuttgart", "köln",
    "cologne", "düsseldorf", "dusseldorf",
    "leipzig", "hannover", "bremen",
    "bonn", "dortmund", "essen",
    "karlsruhe", "mannheim", "nürnberg",
    "nuremberg", "dresden", "augsburg",
    "potsdam", "wiesbaden", "mainz",
    "freiburg", "heidelberg", "ulm",
    "erlangen", "regensburg", "wolfsburg",
    "herzogenaurach", "metzingen",
    "gütersloh", "guetersloh"
]

# İlgilendiğimiz iş alanları
INCLUDE_KEYWORDS = [
    "finance", "financial", "finanz",
    "accountant", "accounting",
    "buchhalter", "buchhaltung",
    "bilanzbuchhalter",
    "controller", "controlling",
    "audit", "auditor", "revision",
    "wirtschaftsprüfer",
    "tax", "steuer",
    "treasury", "investment",
    "banking", "bankkauf",
    "credit analyst", "kredit",
    "insurance", "versicherung",
    "risk manager", "risikomanagement",
    "procurement", "purchasing",
    "einkauf", "einkäufer",
    "supply chain", "logistikmanager",
    "logistics manager",
    "disposition", "disponent",
    "business analyst",
    "business development",
    "consultant", "consulting",
    "unternehmensberater",
    "management consultant",
    "strategy", "strategie",
    "projektmanager", "project manager",
    "projektcontroller",
    "operations manager",
    "commercial manager",
    "kaufmännisch",
    "wirtschaftswissenschaft",
    "volkswirtschaft",
    "economist", "ökonom"
]

# İstemediğimiz pozisyonlar
EXCLUDE_KEYWORDS = [
    "software", "developer", "entwickler",
    "frontend", "backend", "fullstack",
    "full stack", "devops",
    "cybersecurity", "cyber security",
    "it support", "helpdesk",
    "systemadministrator",
    "system administrator",
    "data engineer", "data scientist",
    "machine learning",
    "cloud engineer",
    "software engineer",
    "it consultant", "sap consultant",
    "it projekt", "technical consultant",
    "store manager", "store associate",
    "retail assistant", "verkäufer",
    "verkäuferin", "filialleiter",
    "filialleitung", "kassierer",
    "lagerarbeiter", "lagerhelfer",
    "warehouse worker",
    "kommissionierer", "staplerfahrer",
    "produktionsmitarbeiter",
    "production worker",
    "maschinenbediener",
    "servicekraft", "küchenhilfe"
]


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JobAtlasDE/0.3",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(
        request, timeout=30
    ) as response:
        return json.load(response)


def matches_keyword(text, keyword):
    return re.search(
        r"(?<!\w)" + re.escape(keyword) + r"(?!\w)",
        text
    ) is not None


def is_germany(location):
    location = str(location or "").casefold()

    return any(
        matches_keyword(location, place)
        for place in GERMAN_LOCATIONS
    )


def is_relevant(title):
    title = str(title or "").casefold()

    if any(
        matches_keyword(title, word)
        for word in EXCLUDE_KEYWORDS
    ):
        return False

    return any(
        matches_keyword(title, word)
        for word in INCLUDE_KEYWORDS
    )


def add_job(
    results, seen, job_id, title,
    company, location, url, source
):
    if not job_id or not title or not url:
        return

    if not is_germany(location):
        return

    if not is_relevant(title):
        return

    if job_id in seen:
        return

    seen.add(job_id)

    results.append({
        "id": job_id,
        "title": title,
        "company": company,
        "city": location,
        "language": "unknown",
        "url": url,
        "source": source
    })


def collect_greenhouse(results, seen):
    for company in GREENHOUSE_COMPANIES:
        url = (
            "https://boards-api.greenhouse.io/"
            f"v1/boards/{company}/jobs"
        )

        try:
            data = fetch_json(url)
        except (
            urllib.error.URLError,
            ValueError,
            TimeoutError
        ) as error:
            print(f"Greenhouse error {company}: {error}")
            continue

        for job in data.get("jobs", []):
            location = (
                job.get("location") or {}
            ).get("name", "")

            add_job(
                results,
                seen,
                f"greenhouse-{company}-{job.get('id')}",
                job.get("title", ""),
                company,
                location,
                job.get("absolute_url", ""),
                "greenhouse"
            )


def collect_arbeitnow(results, seen):
    successful_pages = 0

    for page in range(1, ARBEITNOW_PAGES + 1):
        url = (
            "https://www.arbeitnow.com/"
            f"api/job-board-api?page={page}"
        )

        try:
            data = fetch_json(url)
        except (
            urllib.error.URLError,
            ValueError,
            TimeoutError
        ) as error:
            print(f"Arbeitnow page {page}: {error}")
            break

        successful_pages += 1
        jobs = data.get("data", [])

        if not isinstance(jobs, list):
            raise RuntimeError(
                "Unexpected Arbeitnow response"
            )

        for job in jobs:
            slug = job.get("slug", "")
            add_job(
                results,
                seen,
                f"arbeitnow-{slug}",
                job.get("title", ""),
                job.get("company_name", ""),
                job.get("location", ""),
                job.get("url", ""),
                "arbeitnow"
            )

        print(
            f"Arbeitnow page {page}: "
            f"{len(jobs)} jobs checked"
        )

        if not data.get("links", {}).get("next"):
            break

    return successful_pages


def main():
    results = []
    seen = set()

    collect_greenhouse(results, seen)
    greenhouse_count = len(results)

    arbeitnow_pages = collect_arbeitnow(
        results, seen
    )

    # Protect existing data if the new source fails.
    if arbeitnow_pages == 0:
        raise RuntimeError(
            "Arbeitnow unavailable. "
            "Existing jobs.json was not overwritten."
        )

    if not results:
        raise RuntimeError(
            "No matching jobs found. "
            "Existing jobs.json was not overwritten."
        )

    output = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "total": len(results),
        "jobs": results
    }

    with open(
        "jobs.json", "w", encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("Greenhouse jobs:", greenhouse_count)
    print(
        "Arbeitnow jobs:",
        len(results) - greenhouse_count
    )
    print("TOTAL:", len(results))


if __name__ == "__main__":
    main()
