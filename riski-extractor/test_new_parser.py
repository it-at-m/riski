"""Test the new MeetingTagesordnungParser with actual HTML."""

from src.parser.meeting_tagesordnung_parser import MeetingTagesordnungParser

# Load the saved HTML
with open("tagesordnung_9015032.html", "r", encoding="utf-8") as f:
    html = f.read()

parser = MeetingTagesordnungParser()
url = "https://risi.muenchen.de/risi/sitzung/detail/9015032/tagesordnung/oeffentlich"

print("Parsing Tagesordnung...")
print(f"URL: {url}\n")

items = parser.parse(url, html)

print(f"Extracted {len(items)} agenda items:\n")
for item in items:
    print(f"  [{item.number}] {item.name}")
    print(f"       ID: {item.id}")
    print(f"       Order: {item.order}")
    print()

if len(items) > 2:
    print("SUCCESS: Found more than 2 items!")
else:
    print(f"WARNING: Expected more than 2 items, got {len(items)}")
