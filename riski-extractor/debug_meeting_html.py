"""Debug script to analyze actual Meeting HTML structure from RIS."""
import httpx
from bs4 import BeautifulSoup
from config.config import Config, get_config

config = get_config()

# Fetch an actual meeting detail page
meeting_urls = [
    "https://risi.muenchen.de/risi/sitzung/detail/9141571",
    "https://risi.muenchen.de/risi/sitzung/detail/9141572",
]

client = httpx.Client(timeout=10)

for url in meeting_urls:
    print(f"\n{'='*80}")
    print(f"Analyzing: {url}")
    print('='*80)

    try:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all sections
        sections = soup.find_all("section")
        print(f"\nFound {len(sections)} sections:")
        for i, section in enumerate(sections):
            aria_label = section.get("aria-labelledby", "N/A")
            print(f"  {i+1}. aria-labelledby: {aria_label}")

        # Look for agenda-related content
        print("\n--- Looking for Agenda/Tagesordnung content ---")
        for section in sections:
            aria_id = section.get("aria-labelledby", "")
            if "tagesordnung" in aria_id.lower() or "agenda" in aria_id.lower():
                print(f"Found section: {aria_id}")
                # Show structure
                items = section.find_all(["li", "div", "tr"])
                print(f"  Contains {len(items)} li/div/tr elements")
                if items:
                    print(f"  First few items:")
                    for item in items[:5]:
                        text = item.get_text(strip=True)[:100]
                        print(f"    - {text}")

        # Look for any lists
        print("\n--- All lists in page ---")
        lists = soup.find_all(["ul", "ol"])
        print(f"Found {len(lists)} lists")
        for i, lst in enumerate(lists[:3]):
            items = lst.find_all("li")
            print(f"  List {i+1}: {len(items)} items")
            for li in items[:3]:
                text = li.get_text(strip=True)[:100]
                print(f"    - {text}")

        # Look for tables
        print("\n--- All tables in page ---")
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables")

        # Save HTML for manual inspection
        with open(f"meeting_detail_{url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"\nSaved HTML to meeting_detail_{url.split('/')[-1]}.html")

        break  # Only do first URL

    except Exception as e:
        print(f"Error: {e}")

client.close()
