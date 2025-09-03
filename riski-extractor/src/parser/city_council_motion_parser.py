import re
from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Paper
from src.logtools import getLogger
from src.parser.base_parser import BaseParser

DATE_FMT = "%d.%m.%Y"
KB = 1024


class CityCouncilMotionParser(BaseParser[Paper]):
    """
    Parser for City Council Motions
    """

    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("City Council Motions Parser initialized.")

    def _parse_date(self, text: str) -> datetime | None:
        if not text:
            return None
        text = text.strip()
        try:
            return datetime.strptime(text, DATE_FMT)
        except ValueError:
            return None

    def _parse_size_kb(self, fragment: str) -> int | None:
        m = re.search(r"$$(\d+)\s*KB$$", fragment, flags=re.I)
        if m:
            return int(m.group(1)) * KB
        return None

    def _extract_str_code(self, text: str) -> str | None:
        """
        Extracts the code part like '20-26 / A 05870' or '20-26 / F 01283'
        from strings that start with 'StR-Antrag' or 'StR-Anfrage'.
        """
        match = re.search(r"StR-(?:Antrag|Anfrage)\s+([\d\-]+ / [A-Z] \d+)", text)
        if match:
            return match.group(1)
        return None

    def parse(self, url: str, html: str) -> Paper | None:
        soup = BeautifulSoup(html, "html.parser")

        # Title + Reference
        h1 = soup.select_one("h1.page-title")
        name = None
        reference = None
        title = None
        if h1:
            # Subject is in the "Subject" section
            subj = soup.select_one("span.d-inline-block")
            title = subj.get_text(" ", strip=True) if subj else None
            reference = self._extract_str_code(title)
        a_tag = soup.find("a", class_="downloadlink text-nohyphens")
        if a_tag and a_tag.text:
            name = a_tag.text.strip()
        self.logger.debug(name)

        if title:
            if "StR-Antrag" in title:
                return self._parse_antrag(title, reference, name, url, soup)
            elif "StR-Anfrage" in title:
                return self._parse_anfrage(title, reference, name, url, soup)
        # Fallback if nothing matches
        self.logger.warning("Unknown paper type")
        return None

    def _parse_antrag(self, title: str, reference: str, name: str, url: str, soup: BeautifulSoup) -> Paper:
        """Special handling for 'StR-Antrag' papers."""

        a_tag = soup.find("a", class_="downloadlink text-nohyphens")
        file_name = a_tag.text.strip() if a_tag and a_tag.text else None

        date_tag = soup.find("th", string=lambda t: t and "Eingereicht am" in t)
        submitted_date = None
        if date_tag:
            date_value = date_tag.find_next("td")
            if date_value:
                try:
                    submitted_date = datetime.strptime(date_value.get_text(strip=True), "%d.%m.%Y")
                except ValueError:
                    self.logger.warning(f"Could not parse date: {date_value.get_text(strip=True)}")

        originator = None
        org_tag = soup.find("th", string=lambda t: t and "eingereicht von" in t.lower())
        if org_tag:
            originator_cell = org_tag.find_next("td")
            if originator_cell:
                originator = originator_cell.get_text(" ", strip=True)

        paper = Paper(
            id=url,
            type="Antrag",
            name=title,
            reference=reference,
            web=url,
            created=datetime.now(),
            date=submitted_date,
            license=None,
        )

        if originator:
            self.logger.debug(f"Originator found: {originator}")
            # TODO: Lookup in DB  (PaperOriginatorOrgLink oder PaperOriginatorPersonLink)

        if file_name:
            self.logger.debug(f"Main file: {file_name}")
            # TODO: File-Objekt

        return paper

    def _parse_anfrage(self, title: str, reference: str | None, name: str | None, url: str, soup: BeautifulSoup) -> "Paper":
        """
        Processing for City Council Requests.
        """
        self.logger.debug(f"Parsing Anfrage: {reference}")

        # TODO: Extraction of specific data for inquiries
        # Basic metadata (Submitted on, Type, Nature, Deadline, Election period)
        def kv_value(key_label: str) -> str | None:
            for row in soup.select(".keyvalue-container .keyvalue-row"):
                k = row.select_one(".keyvalue-key")
                v = row.select_one(".keyvalue-value")
                if k and v and k.get_text(strip=True).rstrip(":") == key_label.rstrip(":"):
                    return v.get_text(" ", strip=True)
            return None

        gestellt_am = kv_value("Gestellt am:")
        date = self._parse_date(gestellt_am)

        paper_type = kv_value("Typ:")  # "Application"
        # art = kv_value("Art:")           # "Public procedure"
        # frist = kv_value("Bearbeitungs-Frist:")
        # legislative_term = kv_value("Wahlperiode:")
        # originator = kv_value("Gestellt von:")  # can be a person or organization --> TODO: find out what and create
        # direction = kv_value("Zuständiges Referat:")

        # Documents (first document as mainFile)
        main_file: File | None = None
        aux_files: list[File] = []

        for item in soup.select("section#id62 + ul li, section#id62 ul li, section#sectionheader-dokumente + ul li"):
            link = item.select_one("a.downloadlink")
            if not link:
                continue
            href = urljoin(url, link.get("href"))
            filename = link.get_text(" ", strip=True)
            size_text = item.get_text(" ", strip=True)
            size_bytes = self._parse_size_kb(size_text)

            file_obj = File(
                id=href, web=href, name=filename, size=size_bytes, mimeType="application/pdf" if filename.lower().endswith(".pdf") else None
            )
            if main_file is None:
                main_file = file_obj
            else:
                aux_files.append(file_obj)

        created = datetime.now()
        modified = datetime.now()

        paper = Paper(
            id=url,
            web=url,
            body=url,
            type="https://schema.oparl.org/1.1/Paper",
            paperType=paper_type,
            name=name,
            reference=reference,
            date=date,
            mainFile=main_file,
            auxiliaryFile=aux_files,
            created=created,
            modified=modified,
            deleted=False,
        )
        return paper
