# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()
### end of special import block ###

import datetime

import httpx
import stamina

from src.data_models import Meeting
from src.extractor.base_extractor import BaseExtractor
from src.parser.stadtratssitzungen_parser import StadtratssitzungenParser


class StadtratssitzungenExtractor(BaseExtractor[Meeting]):
    """
    Extractor for the RIS website
    """

    def __init__(self) -> None:
        BaseExtractor.__init__(self, "https://risi.muenchen.de/risi/sitzung", "/uebersicht", StadtratssitzungenParser())

    def _get_search_request_params(self) -> dict:
        return {"von": "", "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self, path):
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"}
        response = self.client.post(url=url, data=data)

        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_object_html(self, link: str) -> str:
        response = self.client.get(url=link)  # Detailseite anfragen
        response.raise_for_status()
        return response.text

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter(self, startdate: datetime.date) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")
