import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from core.db.db_access import (
    get_or_create_legislative_term,
    get_or_insert_object_to_database,
    request_object_by_name,
)
from core.model.data_models import File, Keyword, Organization, Paper, PaperSubtypeEnum, PaperTypeEnum

from src.parser.base_parser import BaseParser

# Reference pattern used across antrag detail pages, e.g. "26-32 / B 00059" or "26-32 / V 12345".
_REFERENCE_RE = re.compile(r"\d+-\d+\s*/\s*[A-Z]+\s*\d+")


class BezirksausschussPaperParser(BaseParser[Paper]):
    """
    Parser for papers reachable via the Bezirksausschuss section of the RIS
    (``/antrag/ba/...``): BA-Anträge, BV-Empfehlungen and BV-Anfragen. They all
    share the ``/antrag/detail/<id>`` detail page but differ in their OParl
    paper type, which is supplied by the corresponding extractor.
    """

    def __init__(self, paper_type: PaperTypeEnum, paper_subtype: PaperSubtypeEnum | None = None) -> None:
        super().__init__()
        self.paper_type = paper_type
        self.paper_subtype = paper_subtype
        self.logger.info(f"Bezirksausschuss paper parser initialized for {paper_type}.")

    def _extract_reference(self, text: str | None) -> str | None:
        if not text:
            return None
        match = _REFERENCE_RE.search(text)
        return match.group(0) if match else None

    def _parse_date(self, text: str | None) -> datetime | None:
        if not text:
            return None
        try:
            return datetime.strptime(text.strip(), "%d.%m.%Y")
        except ValueError:
            self.logger.warning(f"Unparseable date: {text!r}")
            return None

    def _ensure_legislative_term(self, text: str | None) -> None:
        """Parse and create/update legislative term if found in text (e.g., '2026-2032')."""
        if not text:
            return
        match = re.search(r"(\d{4})-(\d{4})", text)
        if match:
            term_name = match.group(0)
            try:
                get_or_create_legislative_term(term_name)
                self.logger.debug(f"Ensured legislative term: {term_name}")
            except Exception as e:
                self.logger.warning(f"Could not create legislative term {term_name}: {e!r}")

    def parse(self, url: str, html: str) -> Paper:
        soup = BeautifulSoup(html, "html.parser")

        # --- title and reference ---
        title = self._get_title(soup, self.logger)
        reference = self._extract_reference(title)

        # --- subject (Betreff) ---
        subject = None
        betreff = soup.select_one('section[aria-labelledby="sectionheader-betreff"] div.card-body p')
        if betreff:
            subject = betreff.get_text(" ", strip=True)

        # --- short information (Kurzinfo) ---
        short_information = None
        kurzinfo = soup.select_one('section[aria-labelledby="sectionheader-kurzinfo"] div.collapsable-content')
        if kurzinfo:
            short_information = kurzinfo.get_text(" ", strip=True)

        # --- date: prefer "Beschlossen am", fall back to "Registriert am" ---
        date = self._parse_date(self._kv_value("Beschlossen am:", soup)) or self._parse_date(self._kv_value("Registriert am:", soup))

        # --- subtype ---
        paper_subtype = self.paper_subtype
        paper_subtype_string = self._kv_value("Typ:", soup)
        if paper_subtype is None and paper_subtype_string:
            paper_subtype = self._get_paper_subtype_enum(paper_subtype_string)

        # --- legislative term (Wahlperiode) ---
        wahlperiode = self._kv_value("Wahlperiode:", soup)
        self._ensure_legislative_term(wahlperiode)

        # --- district (Bezirksausschuss / Stadtbezirk) as keyword ---
        district = self._kv_value("Bezirksausschuss:", soup) or self._kv_value("Stadtbezirk/e:", soup)
        keywords = [get_or_insert_object_to_database(Keyword(name=district))] if district else []

        # --- responsible department (Zuständiges Referat) as directing organization ---
        under_direction_of: list[Organization] = []
        referat = self._kv_value("Zuständiges Referat:", soup)
        if referat:
            org = request_object_by_name(name=referat, object_type=Organization)
            if org:
                under_direction_of.append(org)
            else:
                self.logger.debug(f"Directing organization not found in DB: {referat!r}")

        # --- documents ---
        auxiliary_files = []
        for a in soup.select("a.downloadlink[href]"):
            fname = a.get_text(strip=True)
            if fname == "Beschluss.pdf":
                fname = f"Beschluss zu {title}"
            fname = fname.removesuffix(".pdf")
            full_url = urljoin(url, a["href"])
            file = get_or_insert_object_to_database(File(id=full_url, name=fname, fileName=fname, accessUrl=full_url, downloadUrl=full_url))
            auxiliary_files.append(file)

        main_file = auxiliary_files[0] if auxiliary_files else None

        # Create paper with only direct scalar/column fields.
        # Relationships (mainFile, auxiliary_files, keywords, under_direction_of) are set
        # separately and persisted by update_or_insert_objects_to_database in the extractor.
        paper = Paper(
            id=url,
            name=title,
            reference=reference,
            subject=subject,
            short_information=short_information,
            date=date,
            paper_type=self.paper_type,
            paper_subtype=paper_subtype,
        )
        paper.mainFile = main_file
        paper.auxiliary_files = auxiliary_files
        paper.keywords = keywords
        paper.under_direction_of = under_direction_of
        # Initialize remaining relationships
        paper.locations = []
        paper.originator_persons = []
        paper.originator_orgs = []
        paper.related_papers = []
        paper.related_to = []
        paper.super_papers = []
        paper.sub_papers = []

        self.logger.debug(f"Parsed {self.paper_type} {reference} from {url}")
        return paper
