# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules

import datetime
import re

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from truststore import inject_into_ssl

from src.data_models import Person
from src.envtools import getenv_with_exception
from src.logtools import getLogger
from src.parser.city_council_member_parser import CityCouncilMemberParser

inject_into_ssl()
load_dotenv()

### end of special import block ###

import httpx
import stamina


class CityCouncilMemberExtractor:
    """
    Extractor for the city council member on the RIS website
    """

    def __init__(self) -> None:
        self.client = httpx.Client(proxy=getenv_with_exception("HTTP_PROXY"))
        self.logger = getLogger()
        self.ref_parser = CityCouncilMemberParser()
        self.base_url = "https://risi.muenchen.de/risi/person"
        self.city_ciouncil_member_path = "/strmitglieder"
        self.detail_path = "/detail"

    def _extract_city_council_member_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]

        self.logger.info(f"Extracted {len(links)} city council member links from page.")
        return links

    # remove the . from ./xxx
    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return self.base_url + unsanitized_path[1:]

    # remove the . from ./xxx
    def _get_sanitized_detail_url(self, unsanitized_path: str) -> str:
        return self.base_url + self.detail_path + unsanitized_path[1:]

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.city_ciouncil_member_path)
        # evaluate response
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Redirect URL: {redirect_url}")
            self.client.get(url=self._get_sanitized_url(redirect_url))
        else:
            response.raise_for_status()

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

    # iteration through other request
    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_current_page_text(self, path) -> str:
        self.logger.info(f"Sanitize URL with path: {path}")
        response = self.client.get(url=self._get_sanitized_url(path))
        response.raise_for_status()
        return response.text.encode().decode("unicode_escape")

    def _parse_city_council_member_links(self, city_council_member_links: list[str]) -> list[object]:
        city_council_members = []
        for link in city_council_member_links:
            try:
                response = self._get_city_council_member_html(link)
                city_council_member = self.ref_parser.parse(link, response.encode().decode("unicode_escape"))
                city_council_members.append(city_council_member)
            except Exception as e:
                self.logger.error(f"Error parsing {link}: {e}")
        return city_council_members

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter_member(self, startdate: datetime.date) -> str:
        filter_url = self.base_url + "/" + self.city_ciouncil_member_path + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": "", "fraktion": "", "nachname": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()

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
    def _get_next_page(self, path, next_page_link):
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
        self.logger.info(f"Anfrage der naechsten Seite: {page_url}")
        page_response = self.client.get(url=page_url, headers=headers)
        page_response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_city_council_member_html(self, link: str) -> str:
        response = self.client.get(url=link)
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Redirect URL: {redirect_url}")
            response = self.client.get(url=self._get_sanitized_detail_url(redirect_url))
            response.raise_for_status()
            return response.text
        else:
            response.raise_for_status()
            return response.text

    def run(self, startdate: datetime.date) -> list[Person]:
        try:
            # Initial request for cookies, sessionID etc.
            self._initial_request()

            filter_member_redirect_path = self._filter_member(startdate)
            results_per_page_redirect_path = self._set_results_per_page(filter_member_redirect_path)

            # Request and process all city council member
            city_council_member = []
            access_denied = False
            while not access_denied:
                current_page_text = self._get_current_page_text(results_per_page_redirect_path)
                city_council_member_links = self._extract_city_council_member_links(current_page_text)

                if not city_council_member_links:
                    self.logger.warning("No city council member found on the overview.")
                else:
                    city_council_member.extend(self._parse_city_council_member_links(city_council_member_links))

                nav_top_next_link = self._get_next_page_path(current_page_text)

                if not nav_top_next_link:
                    access_denied = True
                    self.logger.info("Keine weiteren Seiten mehr vorhanden - Schleife beendet.")
                    break

                self._get_next_page(path=results_per_page_redirect_path, next_page_link=nav_top_next_link)

            return city_council_member
        except Exception as e:
            self.logger.error(f"Error requesting city council member: {e}")
            return []
