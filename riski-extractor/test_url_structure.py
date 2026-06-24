"""Test the correct URL structure for agenda items."""
from src.parser.meeting_tagesordnung_parser import MeetingTagesordnungParser

# Load the saved HTML
with open("tagesordnung_9015032.html", "r", encoding="utf-8") as f:
    html = f.read()

parser = MeetingTagesordnungParser()
tagesordnung_url = "https://risi.muenchen.de/risi/sitzung/detail/9015032/tagesordnung/oeffentlich"

print("Parsing Tagesordnung...")
print(f"Tagesordnung URL: {tagesordnung_url}\n")

items = parser.parse(tagesordnung_url, html)

print(f"Extracted {len(items)} agenda items:\n")
for item in items:
    print(f"  Item ID: {item.id}")
    print(f"  Number: {item.number}")
    print(f"  Name: {item.name[:70]}")
    print()

# Verify URL structure
expected_base = "https://risi.muenchen.de/risi/sitzung/detail/9015032/tagesordnung/oeffentlich#agenda-"
if items and items[0].id.startswith(expected_base):
    print("SUCCESS: URL structure is correct!")
else:
    print(f"ERROR: URL structure is incorrect")
    print(f"Expected to start with: {expected_base}")
    if items:
        print(f"Got: {items[0].id}")
