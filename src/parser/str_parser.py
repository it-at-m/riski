import locale
import re
from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from src.data_models import Location, Meeting
from src.logtools import getLogger


class STRParser:
    """
    Parser für Stadtratssitzungen
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("STRParser initialized.")

        try:
            locale.setlocale(locale.LC_TIME, "de_DE.utf8")
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, "de_DE")
                self.logger.info("German locale 'de_DE' fallback applied.")
            except locale.Error:
                self.logger.warning("Locale 'de_DE' not available. Date parsing may fail.")

    def parse(self, url: str, html: str) -> Meeting:
        self.logger.info(f"Parsing meeting page: {url}")
        soup = BeautifulSoup(html, "html.parser")

        # --- Title and State ---
        title_element = soup.find("h1", class_="page-title")
        title = title_element.get_text(strip=True) if title_element else "N/A"
        self.logger.debug(f"Parsed title: {title}")

        cancelled = "(entfällt)" in title
        self.logger.debug(f"Meeting cancelled: {cancelled}")

        match = re.search(r"\((.*?)\)", title)
        meetingState = match.group(1) if match else ""
        self.logger.debug(f"Meeting state: {meetingState}")

        # --- Date Parsing ---
        start = datetime.min
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
            type="place",
            name=data_dict.get("Sitzungsort:", "Unbekannt"),
            description="Ort der Stadtratssitzung",
            geojson={},
            streetAddress="",
            room=data_dict.get("Sitzungsort:", ""),
            postalCode="",
            subLocality="",
            locality="München",
            bodies=[],
            organizations=[],
            persons=[],
            meetings=[],
            papers=[],
            license="",
            keyword=[],
            created=datetime.now(),
            modified=datetime.now(),
            web=HttpUrl(url),
            deleted=False,
        )
        self.logger.info("Location object created.")

        # --- Organization (as URLs) ---
        organization_links = soup.select("div.keyvalue-key:-soup-contains('Zuständiges Referat:') + div a")
        organization = [urljoin(url, a.get("href")) for a in organization_links if a.get("href")]
        self.logger.debug(f"Organizations: {organization}")

        # --- Participants (as URLs) ---
        participants = []
        for li in soup.select("div.keyvalue-key:-soup-contains('Vorsitz:') + div ul li a"):
            link = li.get("href")
            if link:
                full_url = urljoin(url, link)
                participants.append(full_url)
        self.logger.debug(f"Participants: {participants}")

        # --- Documents ---
        auxiliaryFile = []
        for doc_link in soup.select("a.downloadlink"):
            doc_url = urljoin(url, doc_link["href"])
            doc_title = doc_link.get_text(strip=True)
            auxiliaryFile.append({"title": doc_title, "url": doc_url})
            self.logger.debug(f"Document found: {doc_title} ({doc_url})")

        # --- Remaining Fields ---
        invitation = {}
        resultsProtocol = {}
        verbatimProtocol = {}
        agendaItem = []
        license = ""
        keyword = []
        created = datetime.min
        modified = datetime.min
        web = HttpUrl(url)
        deleted = False

        # --- Assemble Meeting ---
        meeting = Meeting(
            type=type,
            name=name,
            cancelled=cancelled,
            start=start,
            end=datetime.min,
            location=location,
            organization=organization,
            participant=participants,
            invitation=invitation,
            resultsProtocol=resultsProtocol,
            verbatimProtocol=verbatimProtocol,
            auxiliaryFile=auxiliaryFile,
            agendaItem=agendaItem,
            license=license,
            keyword=keyword,
            created=created,
            modified=modified,
            web=web,
            deleted=deleted,
            meetingState=meetingState,
        )

        self.logger.info(f"Meeting object created: {meeting.name}")
        return meeting


def main():
    return


if __name__ == "__main__":
    main()
