# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()
### end of special import block ###

import datetime
import re

import httpx
import stamina
from bs4 import BeautifulSoup

from src.data_models import ExtractArtifact, Meeting
from src.envtools import getenv_with_exception
from src.logtools import getLogger
from src.parser.stadtratssitzungen_parser import StadtratssitzungenParser


class StadtratssitzungenExtractor:
    """
    Extractor for the RIS website
    """

    def __init__(self) -> None:
        # NOTE: Do not set follow_redirects=True at client level.
        # Some flows inspect 3xx responses/Location; we decide per request.
        self.client = httpx.Client(proxy=getenv_with_exception("HTTP_PROXY"))
        self.logger = getLogger()
        self.str_parser = StadtratssitzungenParser()
        self.base_url = "https://risi.muenchen.de/risi/sitzung"
        self.uebersicht_path = "/uebersicht"

    def _extract_meeting_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]

        self.logger.info(f"Extracted {len(links)} meeting links from page.")
        return links

    def _get_search_request_params(self) -> dict:
        return {"von": "", "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}

    # remove the . from ./xxx
    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return f"{self.base_url}/{unsanitized_path.lstrip('./')}"

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self) -> None:
        # make request
        response = self.client.get(url=self.base_url + self.uebersicht_path, follow_redirects=True)
        response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter_meetings(self, startdate: datetime.date) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.is_redirect:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()
            raise ValueError(f"Expected redirect but got status {response.status_code}")

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self, path) -> str:
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"
        data = {
            "list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"
        }  # 3 is the third entry in a dropdown menu representing the count 100
        response = self.client.post(url=url, data=data)
        if response.is_redirect:
            return response.headers.get("Location")
        else:
            response.raise_for_status()
            raise ValueError(f"Expected redirect but got status {response.status_code}")

    # iteration through other request
    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_current_page_text(self, path) -> str:
        response = self.client.get(url=self._get_sanitized_url(path))
        self.logger.info(f"Request page content: {self._get_sanitized_url(path)}")
        response.raise_for_status()
        return response.text

    def _parse_meeting_links(self, meeting_links: list[str]) -> list[Meeting]:
        meetings = []
        for link in meeting_links:
            self.logger.debug(f"Load meeting link: {link}")
            try:
                response = self._get_meeting_html(link)
                meeting = self.str_parser.parse(link, response.encode().decode("unicode_escape"))
                meetings.append(meeting)
                self.logger.debug(f"Parsed: {meeting.name} ({meeting.start})")
            except Exception as e:
                self.logger.error(f"Error parsing {link}: {e}")
        return meetings

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_meeting_html(self, link: str) -> str:
        response = self.client.get(url=link, follow_redirects=True)  # get detail page
        response.raise_for_status()
        return response.text

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

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_next_page(self, path, next_page_link) -> None:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": self._get_sanitized_url(path),
            "Accept": "text/xml",
            "X-Requested-With": "XMLHttpRequest",
            "Wicket-Ajax": "true",
            "Wicket-Ajax-BaseURL": "sitzung" + path[1:],
            "Wicket-FocusedElementId": "idb",
            "Priority": "u=0",
        }

        page_url = self._get_sanitized_url(next_page_link) + "&_=1"
        self.logger.info(f"Get next page: {page_url}")
        page_response = self.client.get(url=page_url, headers=headers)
        page_response.raise_for_status()

    def run(self, startdate: datetime.date) -> ExtractArtifact:
        try:
            # Initial request for Cookies, SessionID etc.
            # 1. https://risi.muenchen.de/risi/sitzung/uebersicht # for cookies and hallo
            self._initial_request()

            # Request to set Filters
            # 2. https://risi.muenchen.de/risi/sitzung/uebersicht/uebersicht?0-1.-form # get redirect url + filter by datum and domain (only stadtrat)
            filter_sitzungen_redirect_path = self._filter_meetings(startdate)

            # 3. https://risi.muenchen.de/risi/sitzung/uebersicht?1-3.0-list_container-list-card-cardheader-it # set result size to 100
            results_per_page_redirect_path = self._set_results_per_page(filter_sitzungen_redirect_path)

            # request and procss all pages of meetings list
            # 4. iterate over Pages
            access_denied = False
            meetings = []
            while not access_denied:
                current_page_text = self._get_current_page_text(results_per_page_redirect_path)
                meeting_links = self._extract_meeting_links(current_page_text)

                if not meeting_links:
                    self.logger.warning("No Meetings found on overview page.")
                else:
                    meetings.extend(self._parse_meeting_links(meeting_links))

                nav_top_next_link = self._get_next_page_path(current_page_text)

                if not nav_top_next_link:
                    access_denied = True
                    self.logger.info("No further pages found - loop terminated.")
                    break

                self._get_next_page(path=results_per_page_redirect_path, next_page_link=nav_top_next_link)

            return ExtractArtifact(meetings=meetings)
        except Exception as e:
            self.logger.error(f"Error while extracting meetings: {e}")
            return ExtractArtifact(meetings=[])
