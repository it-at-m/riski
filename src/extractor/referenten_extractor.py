# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from truststore import inject_into_ssl

from src.data_models import Person
from src.logtools import getLogger
from src.parser.referenten_parser import ReferentenParser

inject_into_ssl()
load_dotenv()

### end of special import block ###

import httpx
import stamina


class RefExtractor:
    """
    Extractor for the Referent:innen on the RIS website
    """

    def __init__(self) -> None:
        self.client = httpx.Client(proxy="http://internet-proxy-client.muenchen.de:80")
        self.logger = getLogger()
        self.ref_parser = ReferentenParser()
        self.base_url = "https://risi.muenchen.de/risi/person"
        self.referenten_path = "/referenten"
        self.detail_path = "/detail"

    def _extract_referenten_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = [self._get_sanitized_url(a["href"]) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")]

        self.logger.info(f"Extracted {len(links)} meeting links from page.")
        return links

    def _get_headers(self) -> dict:
        return {
            "Host": "risi.muenchen.de",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://risi.muenchen.de",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
        }

    # remove the . from ./xxx
    def _get_sanitized_url(self, unsanitized_path: str) -> str:
        return self.base_url + unsanitized_path[1:]

    # remove the . from ./xxx
    def _get_sanitized_detail_url(self, unsanitized_path: str) -> str:
        return self.base_url + self.detail_path + unsanitized_path[1:]

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.referenten_path)
        # evaluate response
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Redirect URL: {redirect_url}")
            self.client.get(url=self._get_sanitized_url(redirect_url))
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self):
        url = self.base_url + self.referenten_path + "?0-1.0-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list:card:cardheader:itemsperpage_dropdown_top": 3}
        response = self.client.post(url=url, data=data)
        if response.status_code == 302:
            return response.headers.get("Location")
        else:
            response.raise_for_status()

    # iteration through other request
    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_current_page_text(self, path) -> str:
        response = self.client.get(url=self._get_sanitized_url(path))
        self.logger.info(f"Anfrage des Seiteninhalts: {self._get_sanitized_url(path)}")
        response.raise_for_status()
        return response.text.encode().decode("unicode_escape")

    # TODO
    def _parse_ref_links(self, meeting_links: list[str]) -> list[object]:
        meetings = []
        for link in meeting_links:
            try:
                self.logger.info(link)
                response = self._get_referenten_html(link)
                meeting = self.ref_parser.parse(link, response.encode().decode("unicode_escape"))
                meetings.append(meeting)
            except Exception as e:
                self.logger.error(f"Fehler beim Parsen von {link}: {e}")
        return meetings

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_referenten_html(self, link: str) -> str:
        response = self.client.get(url=link)  # Detailseite anfragen
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Redirect URL: {redirect_url}")
            response = self.client.get(url=self._get_sanitized_detail_url(redirect_url))
            response.raise_for_status()
            return response.text
        else:
            response.raise_for_status()
            return response.text

    def run(self) -> list[Person]:
        try:
            # Initiale Anfrage für Cookies, SessionID etc.
            self._initial_request()
            results_per_page_redirect_path = self._set_results_per_page()
            # Anfrage und Verarbeitung aller Seiten der Sitzungsliste
            referenten = []

            current_page_text = self._get_current_page_text(results_per_page_redirect_path)
            ref_links = self._extract_referenten_links(current_page_text)

            if not ref_links:
                self.logger.warning("Keine Referenten auf der Übersichtsseite gefunden.")
            else:
                referenten.extend(self._parse_ref_links(ref_links))

            return referenten
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Referenten: {e}")
            return []
