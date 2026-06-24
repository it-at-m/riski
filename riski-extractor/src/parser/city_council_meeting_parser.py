import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from core.db.db_access import (
    get_or_create_legislative_term,
    get_or_create_location,
    get_or_insert_object_to_database,
    request_object_by_name,
    request_person_by_full_name,
)
from core.model.data_models import AgendaItem, File, Location, Meeting, Organization, Person

from src.parser.base_parser import BaseParser


class CityCouncilMeetingParser(BaseParser[Meeting]):
    """
    Parser for CityCouncilMeetings with AgendaItems, Locations, and Participants
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger.info("CityCouncilMeetingParser initialized.")

    def _extract_person_names(self, text: str) -> tuple[str | None, str | None]:
        if not text:
            return None, None
        clean = re.sub(
            r"\b("
            r"Herr|Frau|Dr\.?|StRin|StR|i\.V\.|BM|BMin|OB|Prof\.?|"
            r"Bürgermeister(in)?|Referent(in)?|Berufsm\.|Fraktionsvorsitzend(e|er)?"
            r")\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        clean = re.sub(r"\.+", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean:
            return None, None
        parts = clean.split()
        if len(parts) >= 2:
            given = " ".join(parts[:-1])
            family = parts[-1]
            return given.strip(), family.strip()
        elif len(parts) == 1:
            return None, parts[0].strip()
        return None, None

    def _resolve_or_create_location(self, location_name: str) -> Location | None:
        try:
            if not location_name or not location_name.strip():
                return None
            location_name = location_name.strip()
            location = get_or_create_location(location_name)
            if location:
                self.logger.info(f"Location resolved/created: {location_name} (id: {location.id}, db_id: {location.db_id})")
            return location
        except Exception as e:
            self.logger.exception(f"Error resolving/creating location '{location_name}'")
            return None

    def _extract_agenda_items(self, soup: BeautifulSoup, meeting_url: str) -> list[AgendaItem]:
        agenda_items = []

        try:
            # Look for agenda sections (typically div with class containing "agenda" or "tagesordnung")
            agenda_section = soup.find("section", {"aria-labelledby": re.compile(r".*agenda.*", re.IGNORECASE)})
            if not agenda_section:
                agenda_section = soup.find("section", {"aria-labelledby": re.compile(r".*tagesordnung.*", re.IGNORECASE)})
            if not agenda_section:
                agenda_section = soup.find("div", {"class": re.compile(r".*agenda.*", re.IGNORECASE)})

            if not agenda_section:
                self.logger.debug("No agenda section found on meeting page")
                return agenda_items

            # Extract agenda items from list items or divs
            item_elements = agenda_section.find_all(["li", "div"], class_=re.compile(r".*item.*", re.IGNORECASE), recursive=True)

            order = 0
            for item_el in item_elements:
                try:
                    if not item_el:
                        continue

                    order += 1
                    text_content = item_el.get_text(strip=True) if item_el else ""

                    if not text_content:
                        continue

                    # Extract agenda item number (e.g., "1.", "1.1", "I.", "A.")
                    number_match = re.search(r"^([0-9IVXiv\-\.]+)", text_content)
                    number = number_match.group(1) if number_match else str(order)

                    # Extract name/title (limit to 500 chars)
                    name = text_content[:500] if text_content else None

                    if not name:
                        continue

                    # Check if public (default: True unless marked otherwise)
                    public = "nicht öffentlich" not in text_content.lower()

                    agenda_item = AgendaItem(
                        id=f"{meeting_url}#agenda-{number}",
                        name=name,
                        number=number,
                        order=order,
                        public=public,
                        deleted=False,
                    )
                    agenda_item.meetings = []
                    agenda_item.keywords = []

                    agenda_items.append(agenda_item)
                    self.logger.debug(f"Extracted AgendaItem: {number} - {name[:50]}")
                except Exception as e:
                    self.logger.debug(f"Error extracting agenda item: {e!r}")
                    continue

        except Exception as e:
            self.logger.debug(f"Error extracting agenda section: {e!r}")

        return agenda_items

    def _extract_participants(self, soup: BeautifulSoup) -> list[Person]:
        participants = []

        try:
            # Look for participant sections
            participant_section = soup.find("section", {"aria-labelledby": re.compile(r".*teilnehmer.*|.*anwesend.*", re.IGNORECASE)})
            if not participant_section:
                self.logger.debug("No participant section found")
                return participants

            # Extract persons from participant list
            person_elements = participant_section.find_all("a", href=re.compile(r"/person/detail/"))

            for person_el in person_elements:
                try:
                    name_text = person_el.get_text(strip=True)
                    given, family = self._extract_person_names(name_text)

                    if not family:
                        continue

                    # Try to find person in DB
                    person = request_person_by_full_name(family, given) if given else None
                    if person:
                        participants.append(person)
                        self.logger.debug(f"Matched participant: {given or ''} {family}")
                    else:
                        self.logger.debug(f"Participant not found in DB: {name_text}")
                except Exception as e:
                    self.logger.debug(f"Error extracting participant: {e!r}")
                    continue
        except Exception as e:
            self.logger.debug(f"Error extracting participants: {e!r}")

        return participants

    def _extract_organizations(self, soup: BeautifulSoup) -> list[Organization]:
        organizations = []

        try:
            # Extract from Zuständiges Referat and Gremium links
            org_elements = soup.select("a[href*='/gremium/']") + soup.select("a[href*='/referat/']")

            for org_el in org_elements:
                try:
                    org_text = org_el.get_text(strip=True) if org_el else None
                    if not org_text:
                        continue

                    # Try to find organization in DB
                    org = request_object_by_name(name=org_text, object_type=Organization)
                    if org:
                        organizations.append(org)
                        self.logger.debug(f"Matched organization: {org_text}")
                    else:
                        self.logger.debug(f"Organization not found in DB: {org_text}")
                except Exception as e:
                    self.logger.debug(f"Error extracting organization: {e!r}")
                    continue
        except Exception as e:
            self.logger.debug(f"Error extracting organizations: {e!r}")

        return organizations

    def parse(self, url: str, html: str) -> Meeting:
        self.logger.debug(f"Parsing meeting page: {url}")
        soup = BeautifulSoup(html, "html.parser")

        # --- Title and State ---
        title_element = soup.find("h1", class_="page-title")
        title = title_element.get_text(strip=True) if title_element else "N/A"
        self.logger.debug(f"Parsed title: {title}")

        cancelled = "(entfällt)" in title
        self.logger.debug(f"Meeting cancelled: {cancelled}")

        match = re.search(r"\((.*?)\)", title)
        meetingState = match.group(1) if match else None
        self.logger.debug(f"Meeting state: {meetingState}")

        # --- Date Parsing ---
        start = None
        match = re.search(r"^(.*?),\s*(\d{1,2}\. .*? \d{4}),\s*(\d{1,2}:\d{2}) Uhr\s*\((.*?)\)", title)
        if match:
            _, date_str, time_str, meetingState = match.groups()
            try:
                start = datetime.strptime(f"{date_str}, {time_str}", "%d. %B %Y, %H:%M")
                self.logger.debug(f"Parsed start time: {start}")
            except ValueError:
                self.logger.exception("Date parsing failed")
        else:
            self.logger.warning("Date format did not match expected pattern.")

        # --- Key-Value Data Extraction ---
        key_value_rows = soup.find_all("div", class_="keyvalue-row")
        data_dict = {}
        for row in key_value_rows:
            key_el = row.find("div", class_="keyvalue-key")
            val_el = row.find("div", class_="keyvalue-value")
            if key_el and val_el:
                key = key_el.get_text(strip=True)
                value = val_el.get_text(strip=True)
                data_dict[key] = value
                self.logger.debug(f"Extracted field: {key} = {value}")

        name = title or f"Meeting {url.split('/')[-1]}"

        # --- Legislative Term (Wahlperiode) ---
        wahlperiode = data_dict.get("Wahlperiode:")
        if wahlperiode:
            try:
                get_or_create_legislative_term(wahlperiode)
            except Exception as e:
                self.logger.debug(f"Could not create legislative term {wahlperiode}: {e!r}")

        # --- Location (Ort der Sitzung) ---
        location_name = data_dict.get("Ort:") or data_dict.get("Sitzungsort:")
        location = self._resolve_or_create_location(location_name) if location_name else None

        # --- Organizations ---
        organizations = self._extract_organizations(soup)

        # --- Participants ---
        participants = self._extract_participants(soup)

        # --- Agenda Items ---
        agenda_items = self._extract_agenda_items(soup, url)

        # --- Documents ---
        auxiliaryFile = []
        for doc_link in soup.select("a.downloadlink"):
            doc_url = urljoin(url, doc_link.get("href", ""))
            doc_title = doc_link.get_text(strip=True)
            doc_title = doc_title.removesuffix(".pdf")
            if doc_url:
                self.logger.debug(f"Document found: {doc_title} ({doc_url})")
                temp_file = File(id=doc_url, name=doc_title, fileName=doc_title, accessUrl=doc_url, downloadUrl=doc_url)
                try:
                    temp_file = get_or_insert_object_to_database(temp_file)
                    auxiliaryFile.append(temp_file)
                    self.logger.debug(f"Saved Document to DB: {doc_title} ({doc_url})")
                except Exception:
                    self.logger.exception(f"Could not save File: {doc_url}")

        # --- Remaining Fields ---
        deleted = False

        # --- Build locations list ---
        locations = [location] if location else []

        # --- Assemble Meeting ---
        meeting = Meeting(
            id=url,
            name=name,
            cancelled=cancelled,
            start=start,
            deleted=deleted,
            meetingState=meetingState,
            auxiliary_files=auxiliaryFile,
            agenda_items=agenda_items,
            organizations=organizations,
            participants=participants,
            locations=locations,
            keywords=[],
        )

        self.logger.info(f"Meeting created: {meeting.name} with {len(agenda_items)} agenda items, {len(participants)} participants, {len(locations)} locations")
        return meeting
