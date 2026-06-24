"""
Extractor that creates AgendaItems from Meeting Templates (Sitzungsvorlagen).
Meeting Templates often contain the agenda items, which can be linked to the actual meetings.
"""

from core.db.db_access import request_all, update_or_insert_objects_to_database
from core.model.data_models import AgendaItem, Paper, PaperTypeEnum

from src.extractor.base_extractor import BaseExtractor
from src.logtools import getLogger
from src.parser.city_council_meeting_template_parser import CityCouncilMeetingTemplateParser


class MeetingTemplateAgendaExtractor:
    """
    Creates AgendaItems from Meeting Templates (Sitzungsvorlagen).
    Extracts agenda structure from template pages and creates agenda items.
    """

    def __init__(self) -> None:
        self.logger = getLogger()
        self.parser = CityCouncilMeetingTemplateParser()
        self.base_extractor = BaseExtractor(
            base_url="https://risi.muenchen.de/risi/sitzungsvorlage",
            base_path="/uebersicht",
            parser=self.parser,
            results_filter_identifier_url="-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top",
            results_filter_identifier_key="list_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.logger.info("MeetingTemplateAgendaExtractor initialized.")

    def run(self) -> None:
        """
        Main extraction loop:
        1. Get all Meeting Templates (Sitzungsvorlagen) from DB
        2. For each template, fetch detail page
        3. Extract agenda items from template content
        4. Save agenda items to DB
        """
        try:
            self.logger.info("Fetching all Meeting Templates from database")
            all_papers = request_all(Paper)

            # Filter to only Meeting Templates
            templates = [p for p in all_papers if p.paper_type == PaperTypeEnum.MEETING_TEMPLATE]
            self.logger.info(f"Found {len(templates)} Meeting Templates")

            if not templates:
                self.logger.warning("No Meeting Templates found in database")
                return

            agenda_items_to_save = []

            for template in templates:
                try:
                    if not template.id:
                        self.logger.debug("Template has no ID, skipping")
                        continue

                    self.logger.debug(f"Processing template: {template.id}")

                    # Fetch detail page
                    try:
                        html = self.base_extractor._get_object_html(template.id)
                    except Exception as e:
                        self.logger.debug(f"Could not fetch template detail page {template.id}: {e!r}")
                        continue

                    # Extract agenda items using parser method
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")

                    # Use same method as meeting parser
                    # This gets the agenda structure from the template
                    agenda_items = self._extract_agenda_from_template(soup, template.id)

                    if not agenda_items:
                        self.logger.debug(f"No agenda items found for template {template.id}")
                        continue

                    # Link agenda items to this template
                    for agenda_item in agenda_items:
                        # Optionally link to meetings - would need cross-reference logic
                        agenda_items_to_save.append(agenda_item)

                    self.logger.debug(f"Extracted {len(agenda_items)} agenda items from template {template.id}")

                except Exception as e:
                    self.logger.exception(f"Error processing template {template.id}: {e!r}")
                    continue

            # Save all agenda items to database
            if agenda_items_to_save:
                self.logger.info(f"Saving {len(agenda_items_to_save)} agenda items from templates to database")
                update_or_insert_objects_to_database(agenda_items_to_save)
                self.logger.info(f"Successfully saved {len(agenda_items_to_save)} agenda items")
            else:
                self.logger.info("No agenda items extracted from any template")

        except Exception as e:
            self.logger.exception(f"Error in MeetingTemplateAgendaExtractor.run(): {e!r}")

    def _extract_agenda_from_template(self, soup, template_url: str) -> list[AgendaItem]:
        """Extract agenda items from a template page."""
        agenda_items = []

        try:
            # Look for any content section that might contain agenda
            sections = soup.find_all("section")

            for section in sections:
                # Find all list items that might be agenda items
                items = section.find_all("li")

                if items:
                    for order, item in enumerate(items, start=1):
                        text = item.get_text(strip=True)
                        if not text:
                            continue

                        # Skip navigation items
                        if len(text) < 5:
                            continue

                        # Create agenda item
                        agenda = AgendaItem(
                            id=f"{template_url}#agenda-{order}",
                            name=text[:500],
                            number=str(order),
                            order=order,
                            public=True,
                            deleted=False,
                        )
                        agenda.meetings = []
                        agenda.keywords = []
                        agenda_items.append(agenda)

            return agenda_items

        except Exception as e:
            self.logger.debug(f"Error extracting agenda from template: {e!r}")
            return []
