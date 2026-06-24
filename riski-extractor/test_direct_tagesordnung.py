"""Test the MeetingTagesordnungExtractor with direct URL construction."""
from src.extractor.meeting_tagesordnung_extractor import MeetingTagesordnungExtractor
from src.parser.meeting_tagesordnung_parser import MeetingTagesordnungParser
import httpx

extractor = MeetingTagesordnungExtractor()

# Test 1: URL construction
print("=" * 80)
print("TEST 1: Tagesordnung URL Construction")
print("=" * 80)

meeting_url = "https://risi.muenchen.de/risi/sitzung/detail/9015032"
tagesordnung_url = extractor._get_tagesordnung_url(meeting_url)

print(f"Meeting URL:        {meeting_url}")
print(f"Tagesordnung URL:   {tagesordnung_url}")

# Test 2: Fetch and parse
print("\n" + "=" * 80)
print("TEST 2: Fetch and Parse Tagesordnung")
print("=" * 80)

try:
    client = httpx.Client(timeout=10)
    response = client.get(tagesordnung_url, follow_redirects=True)
    response.raise_for_status()

    parser = MeetingTagesordnungParser()
    agenda_items = parser.parse(tagesordnung_url, response.text)

    print(f"Status: {response.status_code}")
    print(f"Extracted {len(agenda_items)} agenda items:\n")

    for item in agenda_items:
        print(f"  [{item.number}] {item.name[:70]}")

    if len(agenda_items) >= 4:
        print("\nPASS: Correctly extracted all 4 agenda items!")
    else:
        print(f"\nWARNING: Expected 4 items, got {len(agenda_items)}")

    client.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
