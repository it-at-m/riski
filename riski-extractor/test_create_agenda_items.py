"""Test script to create sample agenda items in the database."""
from config.config import get_config
from core.db.db import init_db
from core.db.db_access import request_all, update_or_insert_objects_to_database
from core.model.data_models import Meeting, AgendaItem


def main():
    config = get_config()
    init_db(config.core.db.database_url)

    # Get all meetings
    meetings = request_all(Meeting)
    print(f"Found {len(meetings)} meetings in database")

    if not meetings:
        print("No meetings found, nothing to do")
        return

    # Create sample agenda items for first 5 meetings
    agenda_items_to_create = []

    for meeting in meetings[:5]:
        print(f"\nCreating agenda items for meeting: {meeting.name}")

        # Create 3 sample agenda items per meeting
        for i in range(1, 4):
            agenda_item = AgendaItem(
                id=f"{meeting.id}#agenda-{i}",
                name=f"Tagesordnungspunkt {i}: Agenda Item {i}",
                number=str(i),
                order=i,
                public=True,
                deleted=False,
            )
            # Link to meeting
            agenda_item.meetings = [meeting]
            agenda_item.keywords = []
            agenda_items_to_create.append(agenda_item)
            print(f"  - Created: {agenda_item.name}")

    # Save to database
    print(f"\nSaving {len(agenda_items_to_create)} agenda items to database...")
    try:
        update_or_insert_objects_to_database(agenda_items_to_create)
        print(f"SUCCESS: Created {len(agenda_items_to_create)} agenda items")

        # Verify they were created
        all_agenda_items = request_all(AgendaItem)
        print(f"\nTotal agenda items in database now: {len(all_agenda_items)}")

    except Exception as e:
        print(f"ERROR: {e!r}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
