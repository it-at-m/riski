import httpx
import stamina
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

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-filtersection_container-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": config.end_date}
        response = self.client.post(url=filter_url, headers=headers, data=data)
        if not response.is_redirect:  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
            raise httpx.HTTPStatusError(
                "Expected redirect from filter request",
                request=response.request,
                response=response,
            )
        return response.headers.get("Location")

    def _extract_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        self.base_url = self.base_url.removesuffix("/str")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("../detail/")]
        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        self.base_url = self.base_url + "/str"
        return links
