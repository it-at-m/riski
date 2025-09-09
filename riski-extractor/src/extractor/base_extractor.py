import re
from abc import ABC
from logging import Logger
from typing import Generic, TypeVar

import httpx
import stamina
from bs4 import BeautifulSoup
from config.config import Config, get_config
from httpx import Client

from src.logtools import getLogger
from src.parser.base_parser import BaseParser

config: Config = get_config()

T = TypeVar("T")


class BaseExtractor(ABC, Generic[T]):
    """
    Base Class for any extractor for the the RIS website.
    Provides the basic extraction functionality and
    abstract methods where individual handling is necessary.
    """

    logger: Logger

    def __init__(
        self, base_url: str, base_path: str, parser: BaseParser[T], results_filter_identifier_url: str, results_filter_identifier_key: str
    ):
        # NOTE: Do not set follow_redirects=True at client level.
        # Some flows inspect 3xx responses/Location; we decide per request.
        if config.https_proxy or config.http_proxy:
            self.client = Client(proxy=config.https_proxy or config.http_proxy, timeout=config.request_timeout)
        else:
            self.client = Client(timeout=config.request_timeout)

        self.logger = getLogger()
        self.base_url = base_url
        self.base_path = base_path
        self.parser = parser
        self.results_filter_identifier_url = results_filter_identifier_url
        self.results_filter_identifier_key = results_filter_identifier_key

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _set_results_per_page(self, path: str):
        url = f"{self._get_sanitized_url(path)}{self.results_filter_identifier_url}"
        data = {self.results_filter_identifier_key: "3"}
        response = self.client.post(url=url, data=data)

        assert response.is_redirect
        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _get_object_html(self, link: str) -> str:
        """
        Method for getting the HTML for parsing. The necessary requests differ
        for some pages, hence some extractors have to implement their own version
        of this method.
        Must return valid HTML, that can be parsed by the Parser provided in __init__
        """
        response = self.client.get(url=link, follow_redirects=True)  # request detail page
        response.raise_for_status()
        return response.text

    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return f"{self.base_url}/{unsanitized_path.lstrip('./')}"

    def run(self) -> list[T]:
        try:
            # Initial request for cookies, sessionID etc.
            self._initial_request()

            filter_redirect_path = self._filter()
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
        except Exception:
            self.logger.exception("Error extracting objects")
            return []

    def _parse_objects_from_links(self, object_links: list[str]) -> list[T]:
        extracted_objects = []
        for link in object_links:
            try:
                response = self._get_object_html(link)
                extracted_object = self.parser.parse(link, response)
                extracted_objects.append(extracted_object)
            except Exception:
                self.logger.exception(f"Error parsing {link}")
        return extracted_objects

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        """
        Base implementation for filtering. If additional filters are needed this method should be overwritten.
        you need to return the redirect-Url, that is found as HTTP-Header "Location".
        This should be a relative path.
        """
        filter_url = self._get_sanitized_url(self.base_path) + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": ""}
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

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.base_path, follow_redirects=True)
        response.raise_for_status()

    def _extract_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]

        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        return links

    def _get_next_page_path(self, current_page_text: str) -> str | None:
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
    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _get_current_page_text(self, path: str) -> str:
        if not path:
            raise ValueError("Empty redirect path detected")
        self.logger.info(f"Request page content: {self._get_sanitized_url(path)}")
        response = self.client.get(url=self._get_sanitized_url(path))
        response.raise_for_status()
        return response.text

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _get_next_page(self, path: str, next_page_link: str):
        headers = {
            "User-Agent": config.user_agent,
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
