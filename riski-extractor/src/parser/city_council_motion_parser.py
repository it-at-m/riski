import re
from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Paper
from src.logtools import getLogger
from src.parser.base_parser import BaseParser

DATE_FORMAT = "%d.%m.%Y"
KILOBYTE = 1024


class CityCouncilMotionParser(BaseParser[Paper]):
    """
    Parser for City Council Motions and Requests.
    Extracts metadata, documents, and relevant information from council pages.
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("City Council Motions Parser initialized.")

    def _parse_date(self, text: str) -> datetime | None:
        """Parse a date string with format dd.mm.yyyy."""
        if not text:
            return None
        text = text.strip()
        try:
            return datetime.strptime(text, DATE_FORMAT)
        except ValueError:
            return None

    def _parse_size_kb(self, fragment: str) -> int | None:
        """Extract file size in KB and convert to bytes."""
        match = re.search(r"(\d+)\s*KB", fragment, flags=re.I)
        if match:
            return int(match.group(1)) * KILOBYTE
        return None

    def _extract_str_code(self, text: str) -> str | None:
        """
        Extract the council code part like '20-26 / A 05870' or '20-26 / F 01283'
        from strings that start with 'StR-Antrag' or 'StR-Anfrage'.
        """
        match = re.search(r"StR-(?:Antrag|Anfrage)\s+([\d\-]+ / [A-Z] \d+)", text)
        if match:
            return match.group(1)
        return None

    def _extract_files(self, url: str, soup: BeautifulSoup) -> tuple[File | None, list[File]]:
        """Extract all file objects (first is main file, rest are auxiliary)."""
        main_file: File | None = None
        auxiliary_files: list[File] = []

        for item in soup.select("section#id62 + ul li, section#id62 ul li, section#sectionheader-dokumente + ul li"):
            link = item.select_one("a.downloadlink")
            if not link:
                continue

            href = urljoin(url, link.get("href"))
            filename = link.get_text(" ", strip=True)
            size_text = item.get_text(" ", strip=True)
            size_bytes = self._parse_size_kb(size_text)

            file_object = File(
                id=href,
                web=href,
                name=filename,
                size=size_bytes,
                mimeType="application/pdf" if filename.lower().endswith(".pdf") else None,
                type="https://schema.oparl.org/1.1/File",
                accessUrl=href,
            )

            if main_file is None:
                main_file = file_object
            else:
                auxiliary_files.append(file_object)

        return main_file, auxiliary_files

    def _extract_date_from_table(self, soup: BeautifulSoup, header_text: str) -> datetime | None:
        """Extract a date from a table row where <th> contains the given header text."""
        header = soup.find("th", string=lambda t: t and header_text in t)
        if header:
            cell = header.find_next("td")
            if cell:
                return self._parse_date(cell.get_text(strip=True))
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        """
        Extracts the description text from the 'Betreff' section.
        """
        section = soup.select_one('section.card[aria-labelledby="sectionheader-betreff"] div.card-body p')
        if section:
            return section.get_text(" ", strip=True)
        return None

    def _kv_value(self, key_label: str, soup: BeautifulSoup) -> str | None:
        """Extracts values from key-value container rows by label."""
        for row in soup.select(".keyvalue-container .keyvalue-row"):
            key = row.select_one(".keyvalue-key")
            value = row.select_one(".keyvalue-value")
            if key and value and key.get_text(strip=True).rstrip(":") == key_label.rstrip(":"):
                return value.get_text(" ", strip=True)
        return None

    def _build_paper(
        self,
        url: str,
        document_name: str | None,
        reference: str | None,
        paper_type: str | None,
        date: datetime | None,
        main_file: File | None,
        auxiliary_files: list[File],
        description: str | None,
    ) -> Paper:
        """Central builder for Paper objects to avoid duplication."""
        created = datetime.now()
        modified = datetime.now()

        return Paper(
            id=url,
            web=url,
            body=url,
            type="https://schema.oparl.org/1.1/Paper",
            paperType=paper_type,
            name=document_name,
            reference=reference,
            date=date,
            mainFile=main_file,
            auxiliaryFile=auxiliary_files,
            created=created,
            modified=modified,
            deleted=False,
            description=description,
        )

    def parse(self, url: str, html: str) -> Paper | None:
        """Main parser entry point. Determines whether the page is a motion or a request."""
        soup = BeautifulSoup(html, "html.parser")

        # Extract page title and subject
        heading = soup.select_one("h1.page-title")
        document_name = None
        reference = None
        title = None

        if heading:
            subject_tag = soup.select_one("span.d-inline-block")
            title = subject_tag.get_text(" ", strip=True) if subject_tag else None
            reference = self._extract_str_code(title) if title else None

        # Extract filename from download link
        link_tag = soup.find("a", class_="downloadlink text-nohyphens")
        if link_tag and link_tag.text:
            document_name = link_tag.text.strip()
        self.logger.debug(document_name)

        # Dispatch to specific parsers
        if title:
            if "StR-Antrag" in title:
                return self._parse_motion(reference, title, url, soup)
            elif "StR-Anfrage" in title:
                return self._parse_request(reference, title, url, soup)

        # Fallback if no type is recognized
        self.logger.warning("Unknown paper type")
        return None

    def _parse_motion(self, reference: str | None, document_name: str | None, url: str, soup: BeautifulSoup) -> Paper:
        submitted_date = self._extract_date_from_table(soup, "Eingereicht am")
        main_file, auxiliary_files = self._extract_files(url, soup)
        return self._build_paper(
            url=url,
            document_name=document_name,
            reference=reference,
            paper_type="Antrag",
            date=submitted_date,
            main_file=main_file,
            auxiliary_files=auxiliary_files,
            description=self._extract_description(soup),
        )

    def _parse_request(self, reference: str | None, document_name: str | None, url: str, soup: BeautifulSoup) -> Paper:
        """Special handling for 'StR-Anfrage' (requests)."""
        self.logger.debug(f"Parsing Anfrage: {reference}")

        submitted_on_text = self._kv_value("Gestellt am:", soup)
        submitted_on = self._parse_date(submitted_on_text)
        paper_type = self._kv_value("Typ:", soup)
        main_file, auxiliary_files = self._extract_files(url, soup)

        return self._build_paper(
            url=url,
            document_name=document_name,
            reference=reference,
            paper_type=paper_type,
            date=submitted_on,
            main_file=main_file,
            auxiliary_files=auxiliary_files,
            description=self._extract_description(soup),
        )
