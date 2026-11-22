
import urllib.request
import urllib.error

URL = "https://jobs.mercedes-benz.com/en"

request = urllib.request.Request(
    URL,
    headers={
        "User-Agent": "JobAtlasDE/0.4",
        "Accept": "text/html"
    }
)

try:
    with urllib.request.urlopen(
        request, timeout=20
    ) as response:
        html = response.read().decode(
            "utf-8", errors="replace"
        )

        print("HTTP status:", response.status)
        print("Page size:", len(html))
        print("Page title found:", "<title" in html.lower())
        print("Job search text found:", "job" in html.lower())

        print("\n--- PAGE PREVIEW ---")
        print(html[:1500])
        print("--- END PREVIEW ---")

except urllib.error.HTTPError as error:
    print("HTTP error:", error.code)

except urllib.error.URLError as error:
    print("Connection error:", error.reason)
