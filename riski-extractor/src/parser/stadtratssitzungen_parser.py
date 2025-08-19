import locale
import platform
import re
from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from src.data_models import File, Location, Meeting
from src.logtools import getLogger
from src.parser.base_parser import BaseParser


class StadtratssitzungenParser(BaseParser[Meeting]):
    """
    Parser für Stadtratssitzungen
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("StadtratssitzungenParser initialized.")

        if platform.system() == "Windows":
            # For Windows, use the specific code page that works
            locale.setlocale(locale.LC_TIME, "German_Germany.1252")  # Or another suitable code page
        else:
            try:
                locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
                self.logger.info("German locale 'de_DE.utf8' applied.")
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, "de_DE")
                    self.logger.info("German locale 'de_DE' fallback applied.")
                except locale.Error:
                    self.logger.warning("Locale 'de_DE' not available. Date parsing may fail.")

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
            except ValueError as e:
                self.logger.error(f"Date parsing failed: {e}")
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

        type = data_dict.get("Gremium:", "Unbekannt")
        name = title

        # --- Location Object ---
        location = Location(
            id=None,
            type="place",
            description="Ort der Stadtratssitzung",
            room=data_dict.get("Sitzungsort:", ""),
            locality="München",
            created=datetime.now(),
            modified=datetime.now(),
            web=HttpUrl(url),
            deleted=False,
        )
        self.logger.debug("Location object created.")

        # --- Organization (as URLs) ---
        organization_links = soup.select("div.keyvalue-key:-soup-contains('Zuständiges Referat:') + div a")
        organization = [HttpUrl(urljoin(url, a.get("href"))) for a in organization_links if a.get("href")]
        organization = organization if len(organization) > 0 else None
        self.logger.debug(f"Organizations: {organization}")

        # --- Participants (as URLs) ---
        participants = []
        for li in soup.select("div.keyvalue-key:-soup-contains('Vorsitz:') + div ul li a"):
            link = li.get("href")
            if link:
                full_url = HttpUrl(urljoin(url, link))
                participants.append(full_url)
        participants = participants if len(participants) > 0 else None
        self.logger.debug(f"Participants: {participants}")

        # --- Documents ---
        auxiliaryFile = []
        for doc_link in soup.select("a.downloadlink"):
            doc_url = HttpUrl(urljoin(url, doc_link["href"]))
            doc_title = doc_link.get_text(strip=True)
            if doc_url:
                auxiliaryFile.append(File(id=doc_url, name=doc_title, accessUrl=doc_url))
            self.logger.debug(f"Document found: {doc_title} ({doc_url})")
        auxiliaryFile = auxiliaryFile if len(auxiliaryFile) > 0 else None

        # --- Remaining Fields ---
        created = datetime.now()
        modified = datetime.now()
        web = HttpUrl(url)
        deleted = False

        # --- Assemble Meeting ---
        meeting = Meeting(
            id=None,
            type=type,
            name=name,
            cancelled=cancelled,
            start=start,
            location=location,
            organization=organization,
            participant=participants,
            auxiliaryFile=auxiliaryFile,
            created=created,
            modified=modified,
            web=web,
            deleted=deleted,
            meetingState=meetingState,
        )

        self.logger.debug(f"Meeting object created: {meeting.name}")
        return meeting
