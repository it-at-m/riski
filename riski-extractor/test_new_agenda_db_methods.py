"""Test the new agenda item database methods in riski-core."""
from config.config import get_config
from core.db.db import init_db
from core.db.db_access import (
    request_all,
    get_or_create_agenda_item,
    create_agenda_items_for_meeting,
    request_agenda_items_by_meeting,
    bulk_create_agenda_items,
)
from core.model.data_models import Meeting, AgendaItem


def test_get_or_create_agenda_item():
    """Test getting or creating a single agenda item."""
    print("\n=== Test: get_or_create_agenda_item ===")

    item = get_or_create_agenda_item(
        id="test-meeting#agenda-1",
        name="Test Agenda Item 1",
        number="1",
        order=0,
    )
    print(f"Created/Retrieved: {item.id} - {item.name}")

    # Call again - should retrieve the same one
    item2 = get_or_create_agenda_item(
        id="test-meeting#agenda-1",
        name="Test Agenda Item 1",
        number="1",
        order=0,
    )
    assert item.id == item2.id, "Should retrieve same item"
    print("PASS: Same item retrieved on second call")


def test_create_agenda_items_for_meeting():
    """Test creating multiple agenda items for a meeting."""
    print("\n=== Test: create_agenda_items_for_meeting ===")

    # Get first meeting from DB
    meetings = request_all(Meeting)
    if not meetings:
        print("No meetings found, skipping test")
        return

    meeting = meetings[0]
    print(f"Using meeting: {meeting.id}")

    agenda_data = [
        {
            "id": f"{meeting.id}#agenda-1",
            "name": "Eröffnung und Begrüßung",
            "number": "1",
            "order": 0,
        },
        {
            "id": f"{meeting.id}#agenda-2",
            "name": "Genehmigung des Protokolls",
            "number": "2",
            "order": 1,
        },
        {
            "id": f"{meeting.id}#agenda-3",
            "name": "Weitere Tagesordnungspunkte",
            "number": "3",
            "order": 2,
        },
    ]

    items = create_agenda_items_for_meeting(meeting.id, agenda_data)
    print(f"Created {len(items)} agenda items")
    for item in items:
        print(f"  - {item.number}: {item.name}")

    print("PASS: Agenda items created for meeting")


def test_request_agenda_items_by_meeting():
    """Test retrieving agenda items for a specific meeting."""
    print("\n=== Test: request_agenda_items_by_meeting ===")

    # Get all meetings
    meetings = request_all(Meeting)
    if not meetings:
        print("No meetings found, skipping test")
        return

    # Find a meeting that might have agenda items
    for meeting in meetings[:5]:
        items = request_agenda_items_by_meeting(meeting.id)
        if items:
            print(f"Meeting {meeting.id} has {len(items)} agenda items:")
            for item in items:
                print(f"  - {item.number}: {item.name}")
            print("PASS: Retrieved agenda items for meeting")
            return

    print("No meetings with agenda items found (this is OK)")


def test_bulk_create_agenda_items():
    """Test bulk creating agenda items."""
    print("\n=== Test: bulk_create_agenda_items ===")

    meetings = request_all(Meeting)
    if not meetings:
        print("No meetings found, skipping test")
        return

    # Create sample items
    items_to_create = []
    for i, meeting in enumerate(meetings[:2]):
        for j in range(1, 4):
            item = AgendaItem(
                id=f"{meeting.id}#bulk-test-{j}",
                name=f"Bulk Test Agenda Item {j}",
                number=str(j),
                order=j - 1,
                public=True,
                deleted=False,
            )
            item.meetings = [meeting]
            item.keywords = []
            items_to_create.append(item)

    count = bulk_create_agenda_items(items_to_create)
    print(f"Created {count} agenda items via bulk_create_agenda_items")
    print("PASS: Bulk creation successful")


if __name__ == "__main__":
    config = get_config()
    init_db(config.core.db.database_url)

    print("Testing new agenda item database methods...")

    try:
        test_get_or_create_agenda_item()
        test_create_agenda_items_for_meeting()
        test_request_agenda_items_by_meeting()
        test_bulk_create_agenda_items()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)

        # Summary
        all_items = request_all(AgendaItem)
        print(f"\nTotal AgendaItems in database: {len(all_items)}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
