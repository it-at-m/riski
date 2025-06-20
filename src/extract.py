# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to inject the truststore before importing the other modules
from dotenv import load_dotenv
from truststore import inject_into_ssl

inject_into_ssl()
load_dotenv()

### end of special import block ###

from logging import Logger

from httpx import Client, HTTPError

from src.logtools import getLogger
from src.parser.str_parser import STRParser


class RISExtractor:
    """
    Extractor for the RIS website
    """

    client: Client
    logger: Logger

    def __init__(self) -> None:
        self.client = Client(proxy="http://internet-proxy-client.muenchen.de:80")
        self.logger = getLogger()

    def run(self, starturl) -> object:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://risi.muenchen.de/risi/aktuelles;jsessionid=69719131B6C58A78576F94C4C79BE292?0",
            "DNT": "1",
            "Connection": "keep-alive",
            "Cookie": "JSESSIONID=69719131B6C58A78576F94C4C79BE292; TS01bf1f22=01021d36f23e894e8dbf03139da8bf38baa9f2c103f587bfd07bf6e281fc44a772f811006104b1a6cf63c67eaa4fd5c00f2e4a20d3fff63f61ac8e8878ddd8c507df28720a32d3eb9ca9bc1c31bef44906ec3446af; BIGSC=!CZZ8PasfiCXK6KRV6YO9XTLAuDl7H4gXAIsd/pXeGlr6wuKtWFV3a79APtoF0jB4qofBsbd83xssE8M=; TS01678d7d=01021d36f2fccc159ee5daf83860baf0d4a6088f9897de055b42f7cfad2630d73b3327d69704e6bdec1e834d1e08e847ef6f29d1a7a90512ad6821775ffc07c4f05617bc67; TS459ee6d1027=087179dd52ab2000f535b67220834db39745c2d1b38ade2249368a93fe803d9077b959aae6576f0d08a4cb704e11300083745f9e6c1019b5fd89082312f7456a499808fe2b395c7939f63a4c725e17647b85dc42234a284a461b9bbedd7a419d",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0, i",
        }

        try:
            response = self.client.get(url=starturl, headers=headers)
            response.raise_for_status()
            strparser = STRParser()
            strparser.parse(url=starturl, html=response.text)
        except HTTPError as e:
            self.logger.error(f"Failed to fetch '{starturl}': {e}")
        return object


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
