from bs4 import BeautifulSoup
from config.config import Config, get_config

from src.data_models import Paper
from src.extractor.base_extractor import BaseExtractor
from src.parser.city_council_motion_parser import CityCouncilMotionParser

config: Config = get_config()


class CityCouncilMotionExtractor(BaseExtractor[Paper]):
    """
    Extractor for the City Council Motion on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/antrag/str",
            "/uebersicht",
            CityCouncilMotionParser(),
            "-2.0-color_container-list-card-cardheader-itemsperpage_dropdown_top",
            "color_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "/uebersicht?0-1.-filtersection_container-form"

    def _extract_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        base_url_without_suffix = self.base_url.removesuffix("/str")
        links = [
            f"{base_url_without_suffix}/{a['href'].lstrip('../')}"
            for a in soup.select("a.headline-link[href]")
            if a["href"].startswith("../detail/")
        ]
        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        return links
