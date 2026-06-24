#!/usr/bin/env python3
"""Test/documentation for Consultation creation (1.4)."""

# Example usage of create_consultation once we have Papers linked to AgendaItems:

# from core.db.db_access import create_consultation

# # Once AgendaItems are linked to a Meeting, and Papers are identified in those items,
# # create a Consultation to link them:
#
# consultation = create_consultation(
#     paper_id="https://risi.muenchen.de/risi/antrag/detail/1234567",
#     agenda_item_id="https://risi.muenchen.de/risi/sitzung/detail/9015032#agenda-1",
#     meeting_id="https://risi.muenchen.de/risi/sitzung/detail/9015032",
#     authoritative=True,  # Was a resolution made?
#     role="Beratung",     # Optional: role of the consultation
# )
#
# This creates an entry in the Consultation table linking the Paper to the AgendaItem.
# The relationship is then available via:
# - Paper.consultations (which Paper is on which AgendaItem)
# - AgendaItem.consultations (which Papers are on this AgendaItem)
# - Meeting.consultations (all consultations in this meeting)

print("Consultation helper function available in db_access.py")
print("See docstring for usage: create_consultation(paper_id, agenda_item_id, meeting_id, ...)")
