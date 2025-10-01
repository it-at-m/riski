import re
from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Keyword, Paper, PaperType, Person
from src.db.db_access import get_or_insert_object_to_database, insert_and_return_object, request_person_by_familyName
from src.logtools import getLogger
from src.parser.base_parser import BaseParser


class CityCouncilMeetingTemplateParser(BaseParser[Paper]):
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("City Council Meeting Template Parser initialized.")

    def _extract_lastname(self, text: str) -> str | None:
        words = text.strip().split()
        ignore = {"Dr.", "Dr", "i.V.", "i.V", "Berufsm.", "Berufsm", "StRin", "Stadtschulrat"}
        filtered = [w for w in words if w not in ignore]
        if not filtered:
            return None
        return filtered[-1]

    def _extract_reference(self, text: str) -> str | None:
        # Regex: digits-digits / V digits
        match = re.search(r"\d+-\d+\s*/\s*V\s*\d+", text)
        return match.group(0) if match else None

    def parse(self, url: str, html: str) -> Paper | None:
        soup = BeautifulSoup(html, "html.parser")

        # --- title and reference ---
        title_text = self._get_title(soup, self.logger)
        reference = self._extract_reference(title_text) if title_text else None

        # --- description / subject (Betreff) ---
        description = None
        description_section = soup.find("section", {"aria-labelledby": "sectionheader-betreff"})
        if description_section:
            description_paragraph = description_section.find("p")
            if description_paragraph:
                description = description_paragraph.get_text(strip=True)

        short_information = None
        short_info_section = soup.find("section", {"aria-labelledby": "sectionheader-kurzinfo"})
        if short_info_section:
            short_info_content = short_info_section.find("div", class_="collapsable-content")
            if short_info_content:
                short_information = short_info_content.get_text(strip=True)

        date_str = self._kv_value("Freigabe:", soup)
        date = datetime.strptime(date_str, "%d.%m.%Y") if date_str else None

        paper_type_string = self._kv_value("Typ:", soup)
        paper_type_fk = get_or_insert_object_to_database(PaperType(name=paper_type_string)).id if paper_type_string else None

        # direction_tag = self._kv_value("Zuständiges Referat:", soup)

        name = self._kv_value("Referent*in:", soup)
        familyName = self._extract_lastname(name) if name else None
        if familyName:
            originators = [request_person_by_familyName(familyName, self.logger)]
            if originators == [None]:
                self.logger.warning(f"{url}: Person not found: {familyName}")
                originators = [insert_and_return_object(Person(id="", familyName=familyName))]
        else:
            originators = []

        # --- locations (Stadtbezirk/e) as keywords ---
        loc_tag = self._kv_value("Stadtbezirk/e:", soup)
        keyword = [get_or_insert_object_to_database(Keyword(name=loc_tag))] if loc_tag else []

        # --- documents ---
        auxiliary_files = []
        doc_links = soup.select("ul.list-group a.downloadlink")
        for a in doc_links:
            fname = a.get_text(strip=True)
            link = a["href"]
            full_url = urljoin(url, link)
            file = get_or_insert_object_to_database(File(id=full_url, name=fname, accessUrl=full_url))
            auxiliary_files.append(file)

        main_file = auxiliary_files[0].db_id if auxiliary_files else None
        self.logger.debug(f"Parsed paper {reference} from {url}")
        paper = Paper(
            id=url,
            name=title_text,
            mainFile=main_file,
            auxiliary_files=auxiliary_files,
            keywords=keyword,
            subject=description,
            paper_type=paper_type_fk,
            date=date,
            originator_persons=originators,
            short_information=short_information,
            reference=reference,
        )
        return paper
