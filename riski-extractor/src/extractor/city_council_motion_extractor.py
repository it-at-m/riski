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
        BaseExtractor.__init__(self, str(config.base_url) + "/antrag/str", "/uebersicht", CityCouncilMotionParser())

    # TODO: no use cause RIS gives the new page in response and not as redirect
    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _set_results_per_page(self, path: str) -> str:
        self.logger.info("Filter Results Per Page")
        url = self.base_url + path + "?1-1.0-color_container-list-card-cardheader-itemsperpage_dropdown_top"
        data = {
            "color_container:list:card:cardheader:itemsperpage_dropdown_top": "3"
        }  # 3 is the third entry in a dropdown menu representing the count 100
        self.client.post(url=url, data=data)
        response = self.client.get(url=self.base_url + self.base_path)
        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    # TODO: no use cause RIS gives the new page in response and not as redirect
    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self._get_sanitized_url(self.base_path) + "?0-2.-filtersection_container-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)
        if not response.is_redirect:
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
