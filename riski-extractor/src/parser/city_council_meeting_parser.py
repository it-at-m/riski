import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Meeting
from src.db.db_access import get_or_insert_object_to_database
from src.parser.base_parser import BaseParser


class CityCouncilMeetingParser(BaseParser[Meeting]):
    """
    Parser for CityCouncilMeetings
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger.info("CityCouncilMeetingParser initialized.")

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

        name = title

        # --- Organization (as URLs) ---
        organization_link_elements = soup.select("div.keyvalue-key:-soup-contains('Zuständiges Referat:') + div a") + soup.select(
            "div.keyvalue-key:-soup-contains('Gremium:') + div a"
        )
        organization_urls = list(dict.fromkeys(urljoin(url, a.get("href")) for a in organization_link_elements if a.get("href"))) or []

        self.logger.debug(f"Organizations: {organization_urls}")

        # --- Documents ---
        auxiliaryFile = []
        for doc_link in soup.select("a.downloadlink"):
            doc_url = urljoin(url, doc_link.get("href", ""))
            doc_title = doc_link.get_text(strip=True)
            if doc_url:
                self.logger.debug(f"Document found: {doc_title} ({doc_url})")
                temp_file = File(id=doc_url, name=doc_title, accessUrl=doc_url)
                try:
                    temp_file = get_or_insert_object_to_database(temp_file)
                    auxiliaryFile.append(temp_file)
                    self.logger.debug(f"Saved Document to DB: {doc_title} ({doc_url})")
                except Exception as e:
                    self.logger.exception(f"Could not save File: {doc_url}. - {e}")

        # --- Remaining Fields ---
        deleted = False

        # --- Assemble Meeting ---
        meeting = Meeting(
            id=url,
            name=name,
            cancelled=cancelled,
            start=start,
            deleted=deleted,
            meetingState=meetingState,
            auxiliary_files=auxiliaryFile,
        )

        self.logger.debug(f"Meeting object created: {meeting.name}")
        return meeting
