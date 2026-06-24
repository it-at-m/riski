"""Parser for Tagesordnung (Agenda) pages of meetings."""
import re
from bs4 import BeautifulSoup
from core.model.data_models import AgendaItem

from src.parser.base_parser import BaseParser
from src.logtools import getLogger


class MeetingTagesordnungParser(BaseParser[AgendaItem]):
    """
    Parses the Tagesordnung (agenda/order of business) page for a meeting.
    These are typically at URLs like: /sitzung/detail/{id}/tagesordnung/oeffentlich
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = getLogger()
        self.logger.info("MeetingTagesordnungParser initialized.")

    def extract_agenda_items(self, html: str, tagesordnung_url: str) -> list[AgendaItem]:
        """
        Extracts all agenda items from a Tagesordnung page.

        The RIS uses a DIV-based table structure with class "d-table" and "d-table-row".

        Args:
            html: The HTML content of the Tagesordnung page
            tagesordnung_url: The Tagesordnung page URL (for item ID generation)

        Returns:
            List of AgendaItem objects extracted from the page.
        """
        agenda_items = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find the main tagesordnung div container (class="d-table tops")
            tagesordnung_container = soup.find("div", class_="tops")

            if not tagesordnung_container:
                self.logger.debug("No tagesordnung container (d-table tops) found")
                return agenda_items

            # Find all rows (d-table-row) - skip the header (topueberschrift)
            rows = tagesordnung_container.find_all("div", class_="d-table-row")

            order = 0
            for row in rows:
                try:
                    # Skip header rows
                    if "topueberschrift" in row.get("class", []):
                        self.logger.debug("Skipping header row")
                        continue

                    order += 1

                    # Extract number from second cell (d-table-cell with span)
                    cells = row.find_all("div", class_="d-table-cell")
                    if len(cells) < 3:
                        continue

                    number_cell = cells[1]
                    number_span = number_cell.find("span")
                    number = number_span.get_text(strip=True) if number_span else str(order)

                    # Extract title from third cell (h3 tag)
                    title_cell = cells[2]
                    title_h3 = title_cell.find("h3", class_="text-keepwhitespace")

                    if not title_h3:
                        self.logger.debug(f"No title found for TOP {number}")
                        continue

                    title = title_h3.get_text(strip=True)

                    if not title:
                        continue

                    # Clean up title if it starts with "TOP - "
                    if title.startswith("TOP - "):
                        title = title[6:]

                    agenda_item = AgendaItem(
                        id=f"{tagesordnung_url}#agenda-{number}",
                        name=title[:500],
                        number=number,
                        order=order,
                        public=True,
                        deleted=False,
                    )
                    agenda_item.meetings = []
                    agenda_item.keywords = []
                    agenda_items.append(agenda_item)
                    self.logger.debug(f"Extracted: {number} - {title[:50]}")

                except Exception as e:
                    self.logger.debug(f"Error extracting row: {e!r}")
                    continue

            if not agenda_items:
                self.logger.debug("No agenda items found on Tagesordnung page")

        except Exception as e:
            self.logger.debug(f"Error parsing Tagesordnung: {e!r}")

        return agenda_items

    def parse(self, tagesordnung_url: str, html: str) -> list[AgendaItem]:
        """
        Main parse method (returns list of AgendaItems).

        Args:
            tagesordnung_url: The Tagesordnung page URL (used as ID for agenda items)
            html: The HTML content
        """
        return self.extract_agenda_items(html, tagesordnung_url)
