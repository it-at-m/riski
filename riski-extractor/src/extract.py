# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
import datetime

from dotenv import load_dotenv
from truststore import inject_into_ssl

from src.data_models import ExtractArtifact
from src.envtools import getenv_with_exception

inject_into_ssl()
load_dotenv()

### end of special import block ###

import re

import httpx
import stamina
from bs4 import BeautifulSoup
from httpx import Client

from src.logtools import getLogger
from src.parser.str_parser import STRParser


class RISExtractor:
    """
    Extractor for the RIS website
    """

    def __init__(self) -> None:
        self.client = Client(proxy=getenv_with_exception("HTTP_PROXY"))
        self.logger = getLogger()
        self.str_parser = STRParser()
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
        return self.base_url + unsanitized_path[1:]

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _initial_request(self):
        # make request
        response = self.client.get(url=self.base_url + self.uebersicht_path)
        # evaluate response
        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Redirect URL: {redirect_url}")
            self.client.get(url=self._get_sanitized_url(redirect_url))
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _filter_sitzungen(self, startdate: datetime.date) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": startdate.isoformat(), "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            self.logger.info(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _set_results_per_page(self, path):
        url = self._get_sanitized_url(path) + "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"}
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

    def _parse_meeting_links(self, meeting_links: list[str]) -> list[object]:
        meetings = []
        for link in meeting_links:
            # self.logger.info(f"Lade Meeting-Link: {link}")
            try:
                response = self._get_meeting_html(link)
                meeting = self.str_parser.parse(link, response.encode().decode("unicode_escape"))
                meetings.append(meeting)
            #   self.logger.info(f"Parsed: {meeting.name} ({meeting.start})")
            except Exception as e:
                self.logger.error(f"Fehler beim Parsen von {link}: {e}")
        return meetings

    @stamina.retry(on=httpx.HTTPError, attempts=5)
    def _get_meeting_html(self, link: str) -> str:
        response = self.client.get(url=link)  # Detailseite anfragen
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

    def run(self, starturl: str, startdate: datetime.date) -> ExtractArtifact:
        try:
            # Initiale Anfrage für Cookies, SessionID etc.
            # 1. https://risi.muenchen.de/risi/sitzung/uebersicht # Für cookies und hallo
            self._initial_request()

            # Anfrage zum Filter Setzen (TODO: StartDatum setzen)
            # 2. https://risi.muenchen.de/risi/sitzung/uebersicht/uebersicht?0-1.-form # redirect url bekommen + filterung nach datum und bereich (nur stadtrat)
            filter_sitzungen_redirect_path = self._filter_sitzungen(startdate)

            # 3. https://risi.muenchen.de/risi/sitzung/uebersicht?1-3.0-list_container-list-card-cardheader-it #Seitengröße auf 100 setzen
            results_per_page_redirect_path = self._set_results_per_page(filter_sitzungen_redirect_path)

            # Anfrage und Verarbeitung aller Seiten der Sitzungsliste
            # 4. durchiterieren durch die Pages
            access_denied = False
            meetings = []
            while not access_denied:
                current_page_text = self._get_current_page_text(results_per_page_redirect_path)
                meeting_links = self._extract_meeting_links(current_page_text)

                if not meeting_links:
                    self.logger.warning("Keine Meetings auf der Übersichtsseite gefunden.")
                else:
                    meetings.extend(self._parse_meeting_links(meeting_links))

                nav_top_next_link = self._get_next_page_path(current_page_text)

                if not nav_top_next_link:
                    access_denied = True
                    self.logger.info("Keine weiteren Seiten mehr vorhanden – Schleife beendet.")
                    break

                self._get_next_page(path=results_per_page_redirect_path, next_page_link=nav_top_next_link)

            return ExtractArtifact(meetings=meetings)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Sitzungen {starturl}: {e}")
            return []


def main() -> None:
    """
    Main function for the extraction process
    """
    logger = getLogger()

    logger.info("Starting extraction process")
    logger.info("Loading sitemap from 'artifacts/sitemap.json'")

    starturl = "https://risi.muenchen.de/"

    extractor = RISExtractor()
    extract_artifact = extractor.run(starturl, datetime.date(2025, 6, 1))

    logger.info("Dumping extraction artifact to 'artifacts/extraction.json'")

    with open("artifacts/extraction.json", "w", encoding="utf-8") as file:
        file.write(extract_artifact.model_dump_json(indent=4))

    logger.info("Extraction process finished")


if __name__ == "__main__":
    main()
