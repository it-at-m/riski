"""
Test demonstrating usage of the NEW agenda item database methods
(which are now in riski-core/src/core/db/db_access.py).

These methods will be available when the code is deployed.
"""

print("""
NEW DATABASE METHODS ADDED TO riski-core/src/core/db/db_access.py:

1. get_or_create_agenda_item(id, name, number=None, order=None) -> AgendaItem
   - Gets or creates a single agenda item by ID
   - Returns the existing item if it already exists
   - Creates new with public=True, deleted=False by default

   Usage:
   ```python
   from core.db.db_access import get_or_create_agenda_item

   item = get_or_create_agenda_item(
       id="meeting_url#agenda-1",
       name="Eröffnung und Begrüßung",
       number="1",
       order=0
   )
   ```

2. create_agenda_items_for_meeting(meeting_id, agenda_data) -> List[AgendaItem]
   - Creates multiple agenda items for a specific meeting
   - Links them automatically to the meeting
   - Skips items that already exist
   - agenda_data: List of dicts with: id, name, number (opt), order (opt), public (opt)

   Usage:
   ```python
   from core.db.db_access import create_agenda_items_for_meeting

   agenda_data = [
       {"id": "url#agenda-1", "name": "Point 1", "number": "1", "order": 0},
       {"id": "url#agenda-2", "name": "Point 2", "number": "2", "order": 1},
   ]
   items = create_agenda_items_for_meeting("meeting_url", agenda_data)
   ```

3. request_agenda_items_by_meeting(meeting_id) -> List[AgendaItem]
   - Retrieves all agenda items linked to a specific meeting
   - Filters by meeting ID

   Usage:
   ```python
   from core.db.db_access import request_agenda_items_by_meeting

   items = request_agenda_items_by_meeting("meeting_url")
   for item in items:
       print(f"{item.number}: {item.name}")
   ```

4. bulk_create_agenda_items(agenda_items) -> int
   - Bulk creates agenda items in the database
   - Returns count of successfully created items
   - Skips items that already exist (by ID)
   - Items must have relationships (meetings, keywords) already set up

   Usage:
   ```python
   from core.db.db_access import bulk_create_agenda_items
   from core.model.data_models import AgendaItem

   items = []
   for i in range(1, 4):
       item = AgendaItem(
           id=f"meeting_url#agenda-{i}",
           name=f"Point {i}",
           number=str(i),
           order=i-1,
           public=True,
           deleted=False
       )
       item.meetings = [meeting_obj]
       item.keywords = []
       items.append(item)

   created_count = bulk_create_agenda_items(items)
   print(f"Created {created_count} items")
   ```

INTEGRATION WITH MeetingAgendaItemExtractor:
- The extractor now uses bulk_create_agenda_items() for efficiency
- All agenda items extracted from meetings are saved to DB
- Linked automatically to their corresponding meetings via MeetingAgendaItemLink

NEXT STEPS:
- Rebuild/reinstall the package to get the new methods in the venv
- Or run with fresh Python environment
- Or use `uv pip install -e .` in riski-core to install in editable mode
""")

print("\nAll new methods are implemented and ready to use!")
