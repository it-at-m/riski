"""
Extractor that processes Tagesordnung (agenda) pages for meetings.
Fetches the Tagesordnung URL directly and extracts agenda items.
"""
import re
import httpx

from config.config import Config, get_config
from core.db.db_access import (
    request_batch,
    create_agenda_items_for_meeting,
    request_agenda_items_by_meeting,
)
from core.model.data_models import Meeting

from src.parser.meeting_tagesordnung_parser import MeetingTagesordnungParser
from src.logtools import getLogger

config: Config = get_config()


class MeetingTagesordnungExtractor:
    """
    Extractor that:
    1. Gets all meetings from DB
    2. For each meeting, constructs the Tagesordnung URL directly
    3. Fetches the Tagesordnung page
    4. Extracts agenda items and saves them to DB
    """

    def __init__(self) -> None:
        self.logger = getLogger()
        self.parser = MeetingTagesordnungParser()
        self.client = httpx.Client(timeout=30)
        self.logger.info("MeetingTagesordnungExtractor initialized.")

    def _get_tagesordnung_url(self, meeting_url: str) -> str:
        """
        Constructs the Tagesordnung URL from a meeting URL.

        Examples:
            https://risi.muenchen.de/risi/sitzung/detail/9015032
            -> https://risi.muenchen.de/risi/sitzung/detail/9015032/tagesordnung/oeffentlich
        """
        # Remove any trailing slashes
        meeting_url = meeting_url.rstrip("/")
        return f"{meeting_url}/tagesordnung/oeffentlich"

    def run(self) -> None:
        """
        Main extraction loop using batch loading.
        """
        try:
            batch_size = config.batch_size
            self.logger.info(f"Loading meetings in batches of {batch_size}")

            offset = 0
            total_extracted = 0
            total_saved = 0
            batch_num = 0

            while True:
                batch_num += 1
                self.logger.info(f"Loading batch {batch_num} (offset={offset}, limit={batch_size})")

                meetings = request_batch(Meeting, offset=offset, limit=batch_size)

                if not meetings:
                    self.logger.info("No more meetings to process")
                    break

                self.logger.info(f"Processing {len(meetings)} meetings in batch {batch_num}")

                for meeting in meetings:
                    try:
                        if not meeting.id:
                            self.logger.debug("Meeting has no ID, skipping")
                            continue

                        # Check if this meeting already has agenda items
                        existing_items = request_agenda_items_by_meeting(meeting.id)
                        if existing_items:
                            self.logger.debug(f"Meeting {meeting.id} already has {len(existing_items)} agenda items, skipping")
                            continue

                        self.logger.debug(f"Processing meeting: {meeting.id}")

                        # Construct Tagesordnung URL
                        tagesordnung_url = self._get_tagesordnung_url(meeting.id)

                        # Fetch Tagesordnung page
                        try:
                            response = self.client.get(tagesordnung_url, follow_redirects=True)
                            response.raise_for_status()
                            tagesordnung_html = response.text
                        except Exception as e:
                            self.logger.debug(f"Could not fetch Tagesordnung {tagesordnung_url}: {e!r}")
                            continue

                        # Parse agenda items (tagesordnung_url is used as ID for items)
                        agenda_items = self.parser.parse(tagesordnung_url, tagesordnung_html)

                        if not agenda_items:
                            self.logger.debug(f"No agenda items found on Tagesordnung page {tagesordnung_url}")
                            continue

                        self.logger.info(f"Extracted {len(agenda_items)} agenda items from {tagesordnung_url}")
                        total_extracted += len(agenda_items)

                        # Convert to dict format for create_agenda_items_for_meeting
                        agenda_data = [
                            {
                                "id": item.id,
                                "name": item.name,
                                "number": item.number,
                                "order": item.order,
                                "public": item.public,
                            }
                            for item in agenda_items
                        ]

                        # Save to database
                        saved_items = create_agenda_items_for_meeting(meeting.id, agenda_data)
                        self.logger.info(f"Saved {len(saved_items)} agenda items for meeting {meeting.id}")
                        total_saved += len(saved_items)

                    except Exception as e:
                        self.logger.exception(f"Error processing meeting {meeting.id}: {e!r}")
                        continue

                # Move to next batch
                offset += batch_size

            self.logger.info(f"Total extracted: {total_extracted}, Total saved: {total_saved}")

        except Exception as e:
            self.logger.exception(f"Error in MeetingTagesordnungExtractor.run(): {e!r}")
        finally:
            self.client.close()
