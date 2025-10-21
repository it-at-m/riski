import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Keyword, Paper, PaperTypeEnum, Person
from src.db.db_access import get_or_insert_object_to_database, insert_and_return_object, request_person_by_familyName
from src.parser.base_parser import BaseParser


class CityCouncilMeetingTemplateParser(BaseParser[Paper]):
    def __init__(self) -> None:
        super().__init__()
        self.logger.info("City Council Meeting Template Parser initialized.")

    def _extract_lastname(self, text: str) -> str | None:
        # In the RIS system, this field appears to be a free-text field.
        # Normally, it contains "Title/Function Lastname", but in some cases "Lastname Function".
        # To handle these exceptional cases, known titles and functions are filtered out.
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

    def parse(self, url: str, html: str) -> Paper:
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
        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                self.logger.warning(f"{url}: Unparseable Freigabe date: {date_str!r}")
        paper_subtype_string = self._kv_value("Typ:", soup)
        paper_subtype = self._get_paper_subtype_enum(paper_subtype_string) if paper_subtype_string else None

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
        doc_links = soup.find_all("a", class_="downloadlink")
        for a in doc_links:
            href = a.get("href")
            if not href:
                continue
            fname = a.get_text(strip=True)
            full_url = urljoin(url, href)
            file = get_or_insert_object_to_database(File(id=full_url, name=fname, accessUrl=full_url, downloadUrl=full_url))
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
            paper_type=PaperTypeEnum.MEETING_TEMPLATE,
            paper_subtype=paper_subtype,
            date=date,
            originator_persons=originators,
            short_information=short_information,
            reference=reference,
        )
        return paper
