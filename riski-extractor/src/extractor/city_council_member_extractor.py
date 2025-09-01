import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Person
from src.extractor.base_extractor import BaseExtractor
from src.parser.city_council_member_parser import CityCouncilMemberParser

config: Config = get_config()


class CityCouncilMemberExtractor(BaseExtractor[Person]):
    """
    Extractor for the city council member on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(str(config.base_url) + "/person", "/strmitglieder", CityCouncilMemberParser())
        self.detail_path = "/detail"

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _set_results_per_page(self, path: str):
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"

        # The '3' corresponds to the third entry of a dropdown menu to select the number items on the page.
        # The entries in the menu are [10, 20, 50, 100]. The Dropdown uses a 0 based index.
        data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"}
        response = self.client.post(url=url, data=data)
        if response.is_redirect:
            return response.headers.get("Location")
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self._get_sanitized_url(self.base_path) + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": "", "fraktion": "", "nachname": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.is_redirect:
            redirect_url = response.headers.get("Location")
            self.logger.debug(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()
