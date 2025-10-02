import locale
import platform
import re
from logging import Logger

from bs4 import BeautifulSoup

from src.data_models import Organization, OrganizationType
from src.logtools import getLogger
from src.parser.base_parser import BaseParser


class CityCouncilFactionParser(BaseParser[Organization]):
    """
    Parser for CityCouncilFactions
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("CityCouncilFactionParser initialized.")

        if platform.system() == "Windows":
            # For Windows, use the specific code page that works
            locale.setlocale(locale.LC_TIME, "German_Germany.1252")
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

    def parse(self, url: str, html: str) -> Organization:
        self.logger.debug(f"Parsing meeting page: {url}")
        url = re.split(r"[\?\&]", url)[0]
        soup = BeautifulSoup(html, "html.parser")

        # --- Title and State ---
        # identify and mark inactive factions
        inactive = "nicht mehr aktiv" in soup.find(class_="titlearea").get_text(strip=True)
        # find title extra info and remove from tree
        title_addon = soup.find("span", class_="page-additionaltitle")
        if title_addon:
            title_addon.decompose()
        title_element = soup.find("h1", class_="page-title")
        title = title_element.get_text(strip=True) if title_element else "N/A"
        self.logger.debug(f"Parsed title: {title}")

        name = title

        # --- Remaining Fields ---
        deleted = False
        organizationType = OrganizationType(name="Fraktion")

        # --- Assemble Faction ---
        faction = Organization(
            id=url,
            name=name,
            classification="Fraktion",
            inactive=inactive,
            deleted=deleted,
            organizationType=organizationType,
        )

        self.logger.debug(f"Meeting object created: {faction.name}")
        return faction
