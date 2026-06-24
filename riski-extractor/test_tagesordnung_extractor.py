"""Test the MeetingTagesordnungExtractor with a real meeting."""
import httpx
from bs4 import BeautifulSoup
from src.parser.meeting_tagesordnung_parser import MeetingTagesordnungParser
from src.extractor.meeting_tagesordnung_extractor import MeetingTagesordnungExtractor

# Test 1: Test finding Tagesordnung link
print("=" * 80)
print("TEST 1: Finding Tagesordnung Link")
print("=" * 80)

extractor = MeetingTagesordnungExtractor()

meeting_url = "https://risi.muenchen.de/risi/sitzung/detail/9139246"

try:
    client = httpx.Client(timeout=10)
    response = client.get(meeting_url, follow_redirects=True)
    response.raise_for_status()

    tagesordnung_link = extractor._find_tagesordnung_link(response.text, meeting_url)

    if tagesordnung_link:
        print(f"Found Tagesordnung link: {tagesordnung_link}")

        # Test 2: Fetch and parse Tagesordnung
        print("\n" + "=" * 80)
        print("TEST 2: Parsing Tagesordnung Page")
        print("=" * 80)

        parser = MeetingTagesordnungParser()

        response2 = client.get(tagesordnung_link, follow_redirects=True)
        response2.raise_for_status()

        agenda_items = parser.parse(tagesordnung_link, response2.text)

        print(f"Extracted {len(agenda_items)} agenda items:")
        for item in agenda_items:
            print(f"  {item.number}: {item.name[:60]}")

        if agenda_items:
            print("\nPASS: Tagesordnung parsing works!")
        else:
            print("\nWARNING: No agenda items extracted")

    else:
        print("No Tagesordnung link found (this meeting may not have a published agenda)")

    client.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
