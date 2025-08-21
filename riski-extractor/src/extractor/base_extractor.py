# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other module
import re
from logging import Logger

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from truststore import inject_into_ssl

from src.envtools import getenv_with_exception
from src.logtools import getLogger

inject_into_ssl()
load_dotenv()

### end of special import block ###

import datetime
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import httpx
import stamina

from src.parser.base_parser import BaseParser

T = TypeVar("T")


class BaseExtractor(ABC, Generic[T]):
    """
    Base Class for any Extractor for the the RIS website.
    This Provides the basic extraction functionalty and
    abstract methods where individual handling is necessary.
    """

    logger: Logger

    def __init__(self, base_url: str, base_path: str, parser: BaseParser[T]):
        # NOTE: Do not set follow_redirects=True at client level.
        # Some flows inspect 3xx responses/Location; we decide per request.
        self.client = httpx.Client(proxy=getenv_with_exception("HTTP_PROXY"))
        self.logger = getLogger()
        self.base_url = base_url
        self.base_path = base_path
        self.parser = parser

    @abstractmethod
    def _set_results_per_page(self, path: str) -> str:
        """
        Method for determinig how many results should be included in the responses.
        More results, lead to less requests and less overhead.
        The necessary request differs between the different pages in the RIS, hence
        every extractor needs to implement their own specific version of it.

        Must return a redirect URL from the HTTP-Header "Location"
        """
        pass

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    @abstractmethod
    def _get_object_html(self, link: str) -> str:
        """
        Method for getting the HTML for parsing. The necessary requests differ
        form page to page, hence every extractor has to implement their own version
        of this method.
        Must return valid HTML, that can be parsed by the Parser provided in __init__
        """
        pass

    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return f"{self.base_url}/{unsanitized_path.lstrip('./')}"

    def run(self, startdate: datetime.date) -> list[T]:
        try:
            # Initial request for cookies, sessionID etc.
            self._initial_request()

            filter_redirect_path = self._filter(startdate)
            results_per_page_redirect_path = self._set_results_per_page(filter_redirect_path)

            # Request and process all extractable objects
            extracted_objects = []
            access_denied = False
            while not access_denied:
                current_page_text = self._get_current_page_text(results_per_page_redirect_path)
                object_links = self._extract_links(current_page_text)

                if not object_links:
                    self.logger.warning("No objects found on the overview page.")
                else:
                    extracted_objects.extend(self._parse_objects_from_links(object_links))

                nav_top_next_link = self._get_next_page_path(current_page_text)

                if not nav_top_next_link:
                    access_denied = True
                    self.logger.info("There are no more pages - exiting loop.")
                    break

                self._get_next_page(path=results_per_page_redirect_path, next_page_link=nav_top_next_link)

            return extracted_objects
        except Exception as e:
            self.logger.error(f"Error extracting objects: {e}")
            return []

    def _parse_objects_from_links(self, city_council_member_links: list[str]) -> list[T]:
        extracted_objects = []
        for link in city_council_member_links:
            try:
                response = self._get_object_html(link)
                extracted_object = self.parser.parse(link, response)
                extracted_objects.append(extracted_object)
            except Exception as e:
                self.logger.error(f"Error parsing {link}: {e}")
        return extracted_objects

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter(self, startdate: datetime.date) -> str:
        """
        Base implementation for filtering. If additional filters are needed this method should be overwritten.
        you need to return the redirect-Url, that is found as HTTP-Header "Location".
        This should be a relative path.
        """
        filter_url = self._get_sanitized_url(self.base_path) + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        # If not raise errror for stamina retry
        if not response.is_redirect:
            raise httpx.HTTPStatusError(
                "Expected redirect from filter request",
                request=response.request,
                response=response,
            )

        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.base_path, follow_redirects=True)
        response.raise_for_status()

    def _extract_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]

        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        return links

    def _get_next_page_path(self, current_page_text) -> str:
        soup = BeautifulSoup(current_page_text, "html.parser")
        scripts = soup.find_all("script")

        ajax_urls = []
        for script in scripts:
            if script.string:
                matches = re.findall(r'Wicket\.Ajax\.ajax\(\{"u":"([^"]+)"', script.string)
                ajax_urls.extend(matches)
        ajax_urls = [u for u in ajax_urls if "nav_top-next" in u]

        if len(ajax_urls) > 0:
            return ajax_urls[0]
        else:
            return None

    # iteration through other request
    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_current_page_text(self, path: str) -> str:
        if not path:
            raise ValueError("Empty redirect path detected")
        self.logger.info(f"Request page content: {self._get_sanitized_url(path)}")
        response = self.client.get(url=self._get_sanitized_url(path))
        response.raise_for_status()
        return response.text

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_next_page(self, path: str, next_page_link):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": self._get_sanitized_url(path),
            "Accept": "text/xml",
            "X-Requested-With": "XMLHttpRequest",
            "Wicket-Ajax": "true",
            "Wicket-FocusedElementId": "idb",
            "Wicket-Ajax-BaseURL": path.lstrip("./"),
            "Priority": "u=0",
        }

        page_url = self._get_sanitized_url(next_page_link) + "&_=1"
        self.logger.debug(f"Request the next page: {page_url}")
        page_response = self.client.get(url=page_url, headers=headers)
        page_response.raise_for_status()
