import re
from datetime import datetime
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlmodel import Session, select

from src.data_models import File, Organization, Paper, Person
from src.parser.base_parser import BaseParser

DATE_FORMAT = "%d.%m.%Y"
KILOBYTE = 1024


class CityCouncilMotionParser(BaseParser[Paper]):
    """
    Parser for council motions and requests.
    Extracts metadata, documents, and references from council information system pages.
    """

    def __init__(self) -> None:
        super().__init__()
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

    def _extract_str_code(self, text: str) -> str | None:
        """
        Extracts the official reference code from strings starting with 'StR-Antrag' or 'StR-Anfrage'.
        """
        match = re.search(r"StR-(?:Antrag|Anfrage)\s+([\d\-]+ / [A-Z] \d+)", text)
        if match:
            return match.group(1)
        return None

    def _extract_files(self, url: str, soup: BeautifulSoup) -> tuple[File | None, list[File]]:
        """Extract all file objects. First one is the main file, the rest are auxiliary."""
        main_file: File | None = None
        auxiliary_files: list[File] = []

        for item in soup.select("section#id62 + ul li, section#id62 ul li, section#sectionheader-dokumente + ul li"):
            link = item.select_one("a.downloadlink")
            if not link:
                continue

            href = urljoin(url, link.get("href"))
            filename = link.get_text(" ", strip=True)

            file_object = File(
                id=href,
                web=href,
                name=filename,
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
        """Extracts the description text from the 'Subject' section."""
        section = soup.select_one('section.card[aria-labelledby="sectionheader-betreff"] div.card-body p')
        if section:
            return section.get_text(" ", strip=True)
        return None

    def _extract_common_metadata(self, soup: BeautifulSoup) -> dict:
        """
        Collects common metadata (date, submitter, responsible office, type).
        """
        submitted_date = self._extract_date_from_table(soup, "Eingereicht am") or self._parse_date(self._kv_value("Gestellt am:", soup))
        originators = self._kv_value("Gestellt von:", soup)
        initiative = self._kv_value("Initiative von:", soup)
        if initiative:
            # Combine both fields if initiative is present
            originators = f"{originators}, {initiative}"
        return {
            "submitted_date": submitted_date,
            "originators": originators,
            "under_direction_of": self._kv_value("Zuständiges Referat:", soup),
            "paper_type": self._kv_value("Typ:", soup),
        }

    def _resolve_persons(self, names_string: str | None, session: Session) -> List[Person]:
        """
        Convert a raw person string into Person objects.
        """
        if not names_string:
            return []

        persons: List[Person] = []
        for raw in names_string.split(","):
            name = raw.strip()
            if not name:
                continue
            # Remove honorifics and council titles
            clean_name = re.sub(r"^(Herr|Frau)?\s*StR(in)?\s*", "", name).strip()
            stmt = select(Person).where(Person.name == clean_name)
            person = session.exec(stmt).first()
            if not person:
                person = Person(name=clean_name)
                session.add(person)
                session.commit()
                session.refresh(person)
            persons.append(person)
        return persons

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
        originator_persons: list[Person],
        originator_orgs: list[Organization],
        under_direction_of: list[Organization],
    ) -> Paper:
        """Central builder for Paper objects."""
        created = datetime.now()
        modified = datetime.now()

        return Paper(
            id=url,
            web=url,
            body=url,
            paperType=paper_type,
            name=document_name,
            reference=reference,
            date=date,
            mainFile=main_file,
            auxiliary_files=auxiliary_files,
            created=created,
            modified=modified,
            deleted=False,
            description=description,
            originator_persons=originator_persons,
        )

    def parse(self, url: str, html: str, session: Session) -> Paper | None:
        soup = BeautifulSoup(html, "html.parser")

        heading = soup.select_one("h1.page-title")
        document_name = None
        reference = None
        title = None

        if heading:
            subject_tag = soup.select_one("span.d-inline-block")
            title = subject_tag.get_text(" ", strip=True) if subject_tag else None
            reference = self._extract_str_code(title) if title else None

        link_tag = soup.find("a", class_="downloadlink text-nohyphens")
        if link_tag and link_tag.text:
            document_name = link_tag.text.strip()
        self.logger.debug(document_name)

        if not title:
            self.logger.warning("Unknown paper type (no title found).")
            return None

        meta = self._extract_common_metadata(soup)
        main_file, auxiliary_files = self._extract_files(url, soup)
        originator_persons = self._resolve_persons(meta["originators"], session)
        originator_orgs = self._resolve_orgs(meta["originators"], session)
        under_direction_of = self._resolve_orgs(meta["under_direction_of"], session)
        # TODO: parse results and link them --> Sitzungsvorlagen need to be parsed
        return self._build_paper(
            url=url,
            document_name=document_name,
            reference=reference,
            paper_type=meta["paper_type"],
            date=meta["submitted_date"],
            main_file=main_file,
            auxiliary_files=auxiliary_files,
            description=self._extract_description(soup),
            originator_persons=originator_persons,
            originator_orgs=originator_orgs,
            under_direction_of=under_direction_of,
        )
