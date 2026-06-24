from core.db.db_access import bulk_create_agenda_items, request_all
from core.model.data_models import Meeting

from src.extractor.base_extractor import BaseExtractor
from src.logtools import getLogger
from src.parser.city_council_meeting_parser import CityCouncilMeetingParser


class MeetingAgendaItemExtractor:
    """
    Extractor that retrieves AgendaItems from existing meetings.
    For each meeting in the database, fetches its detail page and extracts agenda items.
    """

    def __init__(self) -> None:
        self.logger = getLogger()
        self.parser = CityCouncilMeetingParser()
        # Create a base extractor-like client for HTTP requests
        self.base_extractor = BaseExtractor(
            base_url="https://risi.muenchen.de/risi/sitzung",
            base_path="/uebersicht",
            parser=self.parser,
            results_filter_identifier_url="-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top",
            results_filter_identifier_key="list_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.logger.info("MeetingAgendaItemExtractor initialized.")

    def run(self) -> None:
        """
        Main extraction loop:
        1. Get all meetings from DB
        2. For each meeting, fetch detail page
        3. Extract agenda items using parser
        4. Save agenda items to DB
        """
        try:
            self.logger.info("Fetching all meetings from database")
            meetings = request_all(Meeting)
            self.logger.info(f"Found {len(meetings)} meetings")

            if not meetings:
                self.logger.warning("No meetings found in database")
                return

            agenda_items_to_save = []

            for meeting in meetings:
                try:
                    if not meeting.id:
                        self.logger.debug("Meeting has no ID, skipping")
                        continue

                    self.logger.debug(f"Processing meeting: {meeting.id}")

                    # Fetch detail page
                    try:
                        html = self.base_extractor._get_object_html(meeting.id)
                    except Exception as e:
                        self.logger.debug(f"Could not fetch meeting detail page {meeting.id}: {e!r}")
                        continue

                    # Extract agenda items using the parser's method
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")
                    agenda_items = self.parser._extract_agenda_items(soup, meeting.id)

                    if not agenda_items:
                        self.logger.debug(f"No agenda items found for meeting {meeting.id}")
                        continue

                    # Link agenda items to this meeting
                    for agenda_item in agenda_items:
                        agenda_item.meetings = [meeting]
                        agenda_items_to_save.append(agenda_item)

                    self.logger.debug(f"Extracted {len(agenda_items)} agenda items from meeting {meeting.id}")

                except Exception as e:
                    self.logger.exception(f"Error processing meeting {meeting.id}: {e!r}")
                    continue

            # Save all agenda items to database
            if agenda_items_to_save:
                self.logger.info(f"Saving {len(agenda_items_to_save)} agenda items to database")
                created_count = bulk_create_agenda_items(agenda_items_to_save)
                self.logger.info(f"Successfully saved {created_count} agenda items")
            else:
                self.logger.warning("No agenda items extracted from any meeting")

        except Exception as e:
            self.logger.exception(f"Error in MeetingAgendaItemExtractor.run(): {e!r}")
