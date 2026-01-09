import re

from bs4 import BeautifulSoup
from core.model.data_models import Organization, OrganizationClassificationEnum, OrganizationTypeEnum

from src.parser.base_parser import BaseParser


class CityCouncilFactionParser(BaseParser[Organization]):
    """
    Parser for CityCouncilFactions
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger.info("CityCouncilFactionParser initialized.")

    def parse(self, url: str, html: str) -> Organization:
        self.logger.debug(f"Parsing faction page: {url}")
        url = re.split(r"[\?\&]", url)[0]
        soup = BeautifulSoup(html, "html.parser")

        # --- Title and State ---
        # identify and mark inactive factions
        inactive = False
        titlearea = soup.find(class_="titlearea")
        if titlearea:
            inactive = "nicht mehr aktiv" in titlearea.get_text(strip=True)
        # find title extra info and remove from tree
        title_addon = soup.find("span", class_="page-additionaltitle")
        if title_addon:
            title_addon.decompose()
        title_element = soup.find("h1", class_="page-title")
        title = title_element.get_text(strip=True) if title_element else "N/A"
        self.logger.debug(f"Parsed title: {title}")

        name = title

        # --- Remaining Fields ---
        organizationType = OrganizationTypeEnum.FACTION
        classification = OrganizationClassificationEnum.FACTION

        # --- Assemble Faction ---
        faction = Organization(
            id=url,
            name=name,
            classification=classification,
            inactive=inactive,
            organizationType=organizationType,
        )

        self.logger.debug(f"Faction object created: {faction.name}")
        return faction
