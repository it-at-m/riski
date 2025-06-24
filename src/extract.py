# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()

### end of special import block ###

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from httpx import Client

from src.logtools import getLogger
from src.parser.str_parser import STRParser


class RISExtractor:
    """
    Extractor for the RIS website
    """

    def __init__(self) -> None:
        self.client = Client(proxy="http://internet-proxy-client.muenchen.de:80")
        self.logger = getLogger()
        self.str_parser = STRParser()

    def extract_meeting_links(self, html: str) -> list[str]:
        base_url = "https://risi.muenchen.de/risi/sitzung/"
        soup = BeautifulSoup(html, "html.parser")
        links = [
            urljoin(base_url, a["href"].lstrip("./")) for a in soup.select("a.headline-link[href]") if a["href"].startswith("./detail/")
        ]
        self.logger.info(f"Extracted {len(links)} meeting links from page.")
        return links

    def is_access_denied(self, response_text: str) -> bool:
        try:
            root = ET.fromstring(response_text)
            self.logger.debug(f"Parsed XML root tag: {root.tag}")
            redirect = root.findtext("redirect")
            return redirect and "accessdenied" in redirect.lower()
        except ET.ParseError:
            self.logger.debug("Response text is not valid XML, assuming no access denied.")
            return False

    def run(self, starturl) -> object:
        headers = {
            "Host": "risi.muenchen.de",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://risi.muenchen.de",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://risi.muenchen.de/risi/sitzung/uebersicht?35",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
        }

        suche_data = {"von": "", "bis": "", "status": "", "containerBereichDropDown:bereich": "2"}
        base_url = "https://risi.muenchen.de/risi/sitzung"

        try:
            response = self.client.post(url=starturl, headers=headers, data=suche_data)
            if response.status_code == 302:
                redirect_url = response.headers.get("Location")
                self.logger.info(f"Redirect URL: {redirect_url}")
                init_url = base_url + redirect_url[1:]
                redirect_response = self.client.get(url=init_url)
                self.logger.info(f"Response from redirect URL: {redirect_response.status_code}")
            else:
                self.logger.info(f"Response status code: {response.status_code}")
                self.logger.debug(f"Response text: {response.text}")
                redirect_url = None

            if redirect_url:
                result_per_page_url = (
                    base_url
                    + "/uebersicht?"
                    + str(int(redirect_url.split("?")[1]))
                    + "-1.0-list_container-list-card-cardheader-itemsperpage_dropdown_top"
                )
                data = {"list_container:list:card:cardheader:itemsperpage_dropdown_top": "3"}
                first_page_response = self.client.post(url=result_per_page_url, data=data)
                if first_page_response.status_code == 302:
                    redirect_url = first_page_response.headers.get("Location")
                    self.logger.info(f"First Page Redirect URL: {redirect_url}")
                    first_page_redirect_url = base_url + redirect_url[1:]
                    first_page_redirect_response = self.client.get(url=first_page_redirect_url)
                    self.logger.info(f"Response from first page redirect URL: {first_page_redirect_response.status_code}")
                else:
                    self.logger.info(f"Response status code (first page non-redirect): {first_page_response.status_code}")
                    self.logger.debug(f"Response text: {first_page_response.text}")

                first_page_redirect_url = "/uebersicht?" + str(int(first_page_redirect_url.split("?")[1]) + 1)
                suche_url = base_url + first_page_redirect_url + "-1.-form"
                self.logger.info(f"Such-URL: {suche_url}")
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                self.client.post(url=suche_url, headers=headers, data=suche_data)
                suche1_response = self.client.post(url=suche_url, headers=headers, data=suche_data)
                if suche1_response.status_code == 302:
                    redirect_url = suche1_response.headers.get("Location")
                    self.logger.info(f"Suche1 Redirect URL: {redirect_url}")

                access_denied = False
                meetings = []
                while not access_denied:
                    next_page_url = base_url + redirect_url[1:]
                    next_page_response = self.client.get(url=next_page_url)
                    next_page_response.raise_for_status()
                    meeting_links = self.extract_meeting_links(next_page_response.text)
                    if not meeting_links:
                        self.logger.warning("Keine Meetings auf der Übersichtsseite gefunden.")
                    else:
                        for link in meeting_links:
                            self.logger.info(f"Lade Meeting-Link: {link}")
                            try:
                                response = self.client.get(url=link)
                                response.raise_for_status()
                                meeting = self.str_parser.parse(link, response.text)
                                self.logger.info(f"Parsed: {meeting.name} ({meeting.start})")
                            except Exception as e:
                                self.logger.error(f"Fehler beim Parsen von {link}: {e}")

                    soup = BeautifulSoup(next_page_response.text, "html.parser")
                    scripts = soup.find_all("script")

                    ajax_urls = []
                    for script in scripts:
                        if script.string:
                            matches = re.findall(r'Wicket\.Ajax\.ajax\(\{"u":"([^"]+)"', script.string)
                            ajax_urls.extend(matches)

                    last_links = [u for u in ajax_urls if "nav_top-next" in u]
                    if not last_links:
                        access_denied = True
                        self.logger.info("Keine weiteren Seiten mehr vorhanden – Schleife beendet.")
                        break

                    for link in last_links:
                        self.logger.info(f"Gefundene Wicket-URL: {link}")

                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://risi.muenchen.de/risi/sitzung" + redirect_url[1:],
                        "Accept": "text/xml",
                        "X-Requested-With": "XMLHttpRequest",
                        "Wicket-Ajax": "true",
                        "Wicket-Ajax-BaseURL": "sitzung" + redirect_url[1:],
                        "Wicket-FocusedElementId": "idb",
                        "Priority": "u=0",
                    }
                    page_url = base_url + last_links[0][1:] + "&_=1"
                    self.logger.info(f"Anfrage der naechsten Seite: {page_url}")
                    page_response = self.client.get(url=page_url, headers=headers)
                    page_response.raise_for_status()
                    if self.is_access_denied(page_response.text):
                        access_denied = True
                        self.logger.warning("Zugriff verweigert erkannt, Schleife wird beendet.")
                return meetings
            else:
                self.logger.error("Kein Redirect URL erhalten, Abbruch.")
                return []
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Kalenderseite {starturl}: {e}")
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
    extract_artifact = extractor.run(starturl)

    logger.info("Dumping extraction artifact to 'artifacts/extraction.json'")

    with open("artifacts/extraction.json", "w", encoding="utf-8") as file:
        file.write(extract_artifact.model_dump_json(indent=4))

    logger.info("Extraction process finished")


if __name__ == "__main__":
    main()
