import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Meeting
from src.extractor.base_extractor import BaseExtractor
from src.parser.stadtratssitzungen_parser import StadtratssitzungenParser

config: Config = get_config()


class StadtratssitzungenExtractor(BaseExtractor[Meeting]):
    """
    Extractor for Meetings on the RIS website
    """

    def __init__(self) -> None:
        BaseExtractor.__init__(self, str(config.base_url) + "/sitzung", "/uebersicht", StadtratssitzungenParser())

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _set_results_per_page(self, path: str):
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"}
        response = self.client.post(url=url, data=data)
        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")
