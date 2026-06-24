from datetime import datetime

from core.model.data_models import AgendaItem, Location, Meeting

# Test: Create a Meeting with locations and agenda_items
location = Location(id="test-location-1", name="Test Room", deleted=False)
location.meetings = []
location.papers = []
location.organizations = []
location.persons = []
location.bodies = []
location.keywords = []

agenda_item = AgendaItem(id="test-agenda-1", name="Test Agenda Item", number="1", order=1, public=True, deleted=False)
agenda_item.meetings = []
agenda_item.keywords = []

meeting = Meeting(
    id="test-meeting-1",
    name="Test Meeting",
    start=datetime.now(),
    locations=[location],
    agenda_items=[agenda_item],
    organizations=[],
    participants=[],
    keywords=[],
)

print(f"Meeting created: {meeting.name}")
print(f"  - Locations: {len(meeting.locations)}")
print(f"  - Agenda Items: {len(meeting.agenda_items)}")
print("Test PASSED")
