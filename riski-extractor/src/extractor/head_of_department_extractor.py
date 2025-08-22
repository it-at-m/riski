# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
import datetime

from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()
### end of special import block ###

import httpx
import stamina

from src.data_models import Person
from src.extractor.base_extractor import BaseExtractor
from src.parser.head_of_department_parser import HeadOfDepartmentParser


class HeadOfDepartmentExtractor(BaseExtractor[Person]):
    """
    Extractor for the Heads of Departments on the RIS website
    """

    def __init__(self) -> None:
        BaseExtractor.__init__(self, "https://risi.muenchen.de/risi/person", "/referenten", HeadOfDepartmentParser())

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self, path: str) -> str:
        url = self.base_url + self.base_path + "?0-1.0-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list:card:cardheader:itemsperpage_dropdown_top": 3}  # 3 is the third entry in a dropdown menu representing the count 100
        response = self.client.post(url=url, data=data)
        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter(self, startdate: datetime.date) -> str:
        pass

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_object_html(self, link: str) -> str:
        response = self.client.get(url=link, follow_redirects=True)  # Request detailpage
        response.raise_for_status()
        return response.text
