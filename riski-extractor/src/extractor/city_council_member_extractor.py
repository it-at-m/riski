# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules

import datetime

from dotenv import load_dotenv
from truststore import inject_into_ssl

from src.data_models import Person
from src.parser.city_council_member_parser import CityCouncilMemberParser

inject_into_ssl()
load_dotenv()

### end of special import block ###

import httpx
import stamina

from src.extractor.base_extractor import BaseExtractor


class CityCouncilMemberExtractor(BaseExtractor[Person]):
    """
    Extractor for the city council member on the RIS website
    """

    def __init__(self) -> None:
        BaseExtractor.__init__(self, "https://risi.muenchen.de/risi/person", "/strmitglieder", CityCouncilMemberParser())
        self.detail_path = "/detail"

    def _get_sanitized_detail_url(self, unsanitized_path: str):
        return f"{self.base_url}{self.detail_path}/{unsanitized_path.lstrip('./')}"

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self, path: str):
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"

        # The '3' corresponds to the third entry of a dropdown menu to select the number items on the page.
        # The entries in the menu are [10, 20, 50, 100]. The Dropdown uses a 0 based index.
        data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": 3}
        response = self.client.post(url=url, data=data)
        if response.status_code == 302:
            return response.headers.get("Location")
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter(self, startdate: datetime.date) -> str:
        filter_url = self._get_sanitized_url(self.base_path) + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": "", "fraktion": "", "nachname": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.debug(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_object_html(self, link: str) -> str:
        response = self.client.get(url=link)
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.debug(f"Redirect URL: {redirect_url}")
            response = self.client.get(url=self._get_sanitized_detail_url(redirect_url))
            response.raise_for_status()
            return response.text
        else:
            response.raise_for_status()
            return response.text
