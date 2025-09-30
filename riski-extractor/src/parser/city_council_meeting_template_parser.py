from datetime import datetime
from logging import Logger
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Keyword, Paper, PaperType
from src.db.db_access import get_or_insert_object_to_database
from src.logtools import getLogger
from src.parser.base_parser import BaseParser


class CityCouncilMeetingTemplateParser(BaseParser[Paper]):
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("City Council Meeting Template Parser initialized.")

    def parse(self, url: str, html: str) -> Paper | None:
        soup = BeautifulSoup(html, "html.parser")

        # --- title and reference ---
        title_text = self._get_title(soup, self.logger)
        reference = title_text.split(" ", 1)[-1] if " " in title_text else title_text

        # --- description / subject (Betreff) ---
        desc_tag = soup.select_one("#sectionheader-betreff + .card-body p")
        description = desc_tag.get_text(" ", strip=True) if desc_tag else None

        date_str = self._kv_value("Freigabe:", soup)
        date = datetime.strptime(date_str, "%d.%m.%Y") if date_str else None

        paper_type_string = self._kv_value("Typ:", soup)
        paper_type_fk = get_or_insert_object_to_database(PaperType(name=paper_type_string)).id if paper_type_string else None

        # direction_tag = self._kv_value("Zuständiges Referat:", soup)

        # referent = self._kv_value("Referent*in:", soup)
        # originators = [Person(name=referent)] if referent else []

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
            main_file=main_file,
            auxiliary_files=auxiliary_files,
            keywords=keyword,
            description=description,
            paper_type=paper_type_fk,
            date=date,
        )
        return paper
