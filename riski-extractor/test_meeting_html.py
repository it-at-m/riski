import sys
sys.path.insert(0, '/home/runner/riski/riski-core/src')  # Ensure core is imported from source

from src.parser.city_council_meeting_parser import CityCouncilMeetingParser
from datetime import datetime

# Sample HTML from a real Munich RIS meeting page (simplified)
sample_html = """
<html>
<head><title>Test Meeting</title></head>
<body>
<h1 class="page-title">Stadtrat, Donnerstag, 15. Januar 2026, 09:30 Uhr (öffentlich)</h1>

<section aria-labelledby="sectionheader-betreff">
    <div class="card-body">
        <div class="keyvalue-row">
            <div class="keyvalue-key">Wahlperiode:</div>
            <div class="keyvalue-value">2024 - 2030</div>
        </div>
        <div class="keyvalue-row">
            <div class="keyvalue-key">Ort:</div>
            <div class="keyvalue-value">Rathaus, Großer Sitzungssaal</div>
        </div>
    </div>
</section>

<section aria-labelledby="sectionheader-tagesordnung">
    <div class="list-group">
        <li class="list-group-item">1. Begrüßung</li>
        <li class="list-group-item">2. Genehmigung des Protokolls</li>
        <li class="list-group-item">3. Anträge und Anfragen</li>
    </div>
</section>

<section aria-labelledby="sectionheader-teilnehmer">
    <div class="participant-list">
        <a href="/person/detail/123">Max Mustermann</a>
        <a href="/person/detail/456">Anna Mueller</a>
    </div>
</section>

<a href="/gremium/detail/789">Stadtrat</a>

<a class="downloadlink" href="protocol.pdf">Protokoll.pdf</a>
</body>
</html>
"""

parser = CityCouncilMeetingParser()
result = parser.parse("https://risi.muenchen.de/risi/sitzung/detail/12345", sample_html)

print(f"Parsed Meeting: {result.name}")
print(f"  ID: {result.id}")
print(f"  Start: {result.start}")
print(f"  Agenda Items: {len(result.agenda_items)}")
print(f"  Locations: {len(result.locations) if hasattr(result, 'locations') else 'N/A (not loaded)'}")
print(f"  Organizations: {len(result.organizations)}")
print(f"  Participants: {len(result.participants)}")
print(f"  Files: {len(result.auxiliary_files)}")
