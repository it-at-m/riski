# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()
### end of special import block ###

import httpx
import stamina
from bs4 import BeautifulSoup

from src.data_models import Person
from src.envtools import getenv_with_exception
from src.logtools import getLogger
from src.parser.head_of_department_parser import HeadOfDepartmentParser


class HeadOfDepartmentExtractor:
    """
    Extractor for the Heads of Departments on the RIS website
    """

    def __init__(self) -> None:
        # NOTE: Do not set follow_redirects=True at client level.
        # Some flows inspect 3xx responses/Location; we decide per request.
        self.client = httpx.Client(proxy=getenv_with_exception("HTTP_PROXY"))
        self.logger = getLogger()
        self.head_of_department_parser = HeadOfDepartmentParser()
        self.base_url = "https://risi.muenchen.de/risi/person"
        self.referenten_path = "/referenten"

    def _extract_head_of_department_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        raw = [a["href"] for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]
        links = list(dict.fromkeys(self._get_sanitized_url(href) for href in raw))

        self.logger.info(f"Extracted {len(links)} Head of Department links from page.")
        return links

    # remove the . from ./xxx
    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return f"{self.base_url}/{unsanitized_path.lstrip('./')}"

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.referenten_path, follow_redirects=True)
        response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self) -> str:
        url = self.base_url + self.referenten_path + "?0-1.0-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list:card:cardheader:itemsperpage_dropdown_top": 3}  # 3 is the third entry in a dropdown menu representing the count 100
        response = self.client.post(url=url, data=data)
        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    # iteration through other request
    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_current_page_text(self, path: str) -> str:
        if not path:
            raise ValueError("Empty redirect path detected")
        self.logger.info(f"Request page content: {self._get_sanitized_url(path)}")
        response = self.client.get(url=self._get_sanitized_url(path))
        response.raise_for_status()
        return response.text

    def _parse_head_of_departments(self, head_of_department_links: list[str]) -> list[Person]:
        heads_of_departments: list[Person] = []
        for link in head_of_department_links:
            try:
                self.logger.info(link)
                response = self._get_head_of_department_html(link)
                head_of_department = self.head_of_department_parser.parse(link, response)
                heads_of_departments.append(head_of_department)
            except Exception:
                self.logger.exception(f"Error parsing {link}")
        return heads_of_departments

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_head_of_department_html(self, link: str) -> str:
        response = self.client.get(url=link, follow_redirects=True)  # Request detailpage
        response.raise_for_status()
        return response.text

    def run(self) -> list[Person]:
        try:
            # Initial request for cookies, sessionID etc.
            self._initial_request()
            results_per_page_redirect_path = self._set_results_per_page()
            # Request and process the single overview page (Munich has ~15 departments; index 3 = 100 items)
            heads_of_departments: list[Person] = []

            current_page_text = self._get_current_page_text(results_per_page_redirect_path)
            ref_links = self._extract_head_of_department_links(current_page_text)

            if not ref_links:
                self.logger.warning("No Heads of Departments found on the overview page.")
            else:
                heads_of_departments.extend(self._parse_head_of_departments(ref_links))

            return heads_of_departments
        except Exception:
            self.logger.exception("Error requesting Heads of Departments")
            return []
