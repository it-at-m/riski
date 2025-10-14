import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Keyword, Organization, Paper, PaperSubtype, PaperType, Person
from src.db.db_access import get_or_insert_object_to_database, request_object_by_name, request_person_by_full_name
from src.parser.base_parser import BaseParser


class CityCouncilMotionParser(BaseParser[Paper]):
    def __init__(self) -> None:
        super().__init__()
        self.logger.info("City Council Motions Parser initialized.")

    def _extract_person_names(self, text: str) -> tuple[str | None, str | None]:
        if not text:
            return None, None
        clean = re.sub(
            r"\b("
            r"Herr|Frau|Dr\.?|StRin|StR|i\.V\.|BM|BMin|OB|Prof\.?|"
            r"Bürgermeister(in)?|Referent(in)?|Berufsm\.|Fraktionsvorsitzend(e|er)?"
            r")\b",
            "",
            text,
            flags=re.IGNORECASE,
        )

        clean = re.sub(r"\.+", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean:
            return None, None
        parts = clean.split()
        self.logger.debug(parts)
        if len(parts) >= 2:
            given = " ".join(parts[:-1])
            family = parts[-1]
            return given.strip(), family.strip()
        elif len(parts) == 1:
            return None, parts[0].strip()
        return None, None

    def _extract_reference(self, text: str) -> str | None:
        match = re.search(r"StR-(?:Antrag|Anfrage)\s+([\d\-]+ / [A-Z] \d+)", text)
        return match.group(1) if match else None

    def _detect_paper_type(self, text: str | None) -> str:
        """Erkennt, ob es ein StR-Antrag oder StR-Anfrage ist."""
        if not text:
            return "StR-Antrag/Anfrage"
        text_lower = text.lower()
        if "str-anfrage" in text_lower:
            return "StR-Anfrage"
        elif "str-antrag" in text_lower:
            return "StR-Antrag"
        return "StR-Antrag/Anfrage"

    def _parse_date(self, text: str) -> datetime | None:
        if not text:
            return None
        text = text.strip()
        try:
            return datetime.strptime(text, "%d.%m.%Y")
        except ValueError:
            return None

    def _split_originators(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        cleaned = re.sub(r"\s+und\s+", ",", raw)
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        return parts

    def _resolve_originators(self, originator_text: str | None) -> tuple[list[Person], list[Organization]]:
        """
        Attempts to match each entry first as an organization, then as a person.

        Logs an error if neither exists in the database.
        """
        persons: list[Person] = []
        orgs: list[Organization] = []

        if not originator_text:
            return persons, orgs

        for entry in self._split_originators(originator_text):
            clean_entry = entry.strip()
            if not clean_entry:
                continue

            # 1. Try to find organization in DB
            org = request_object_by_name(name=clean_entry, object_type=Organization)
            if org:
                orgs.append(org)
                self.logger.debug(f"Matched organization: {clean_entry}")
                continue

            # 2. Try to find person in DB (first name + last name)
            given, family = self._extract_person_names(clean_entry)
            if family:
                person = request_person_by_full_name(familyName=family, givenName=given, logger=self.logger)
                if person:
                    persons.append(person)
                    self.logger.debug(f"Matched person: {given or ''} {family}")
                    continue

            # 3. No match → log error
            self.logger.error(f"Originator not found in DB (neither person nor organization): '{clean_entry}'")

        return persons, orgs

    # --- main parse ---
    def parse(self, url: str, html: str) -> Paper:
        soup = BeautifulSoup(html, "html.parser")

        # --- title and reference ---
        heading = soup.select_one("h1.page-title")
        title = None
        reference = None
        if heading:
            subject_tag = soup.select_one("span.d-inline-block")
            title = subject_tag.get_text(" ", strip=True) if subject_tag else None
            reference = self._extract_reference(title) if title else None

        # --- determine type (Antrag vs Anfrage) ---
        paper_type_str = self._detect_paper_type(title)
        paper_type_fk = get_or_insert_object_to_database(PaperType(name=paper_type_str)).id

        # --- description / subject ---
        description = None
        desc_section = soup.select_one('section.card[aria-labelledby="sectionheader-betreff"] div.card-body p')
        if desc_section:
            description = desc_section.get_text(" ", strip=True)

        # --- date ---
        date_str = self._kv_value("Gestellt am:", soup)
        date = self._parse_date(date_str)

        # --- subtype ---
        paper_subtype_string = self._kv_value("Typ:", soup)
        paper_subtype_fk = (
            get_or_insert_object_to_database(PaperSubtype(name=paper_subtype_string, paper_type_id=paper_type_fk)).id
            if paper_subtype_string
            else None
        )

        # --- originators (persons + orgs) ---
        originator_text = self._kv_value("Gestellt von:", soup)
        originator_persons, originator_orgs = self._resolve_originators(originator_text)
        initiative_text = self._kv_value("Initiative:", soup)
        if initiative_text:
            initative_persons, initiaive_orgs = self._resolve_originators(initiative_text)
            unique_persons = {p.id: p for p in originator_persons}  # dict: id → Objekt
            for p in initative_persons:
                unique_persons.setdefault(p.id, p)
            originator_persons = list(unique_persons.values())

            # Für Organisationen ähnlich
            unique_orgs = {o.id: o for o in originator_orgs}
            for o in initiaive_orgs:
                unique_orgs.setdefault(o.id, o)
            originator_orgs = list(unique_orgs.values())

        # --- keywords ---
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
        # --- build Paper object ---
        paper = Paper(
            id=url,
            name=title,
            mainFile=main_file,
            auxiliary_files=auxiliary_files,
            keywords=keyword,
            subject=description,
            paper_type=paper_type_fk,
            paper_subtype=paper_subtype_fk,
            date=date,
            originator_persons=originator_persons,
            originator_organizations=originator_orgs,
            reference=reference,
            paperType=paper_type_str,
        )

        self.logger.debug(f"Parsed {paper_type_str} {reference} from {url}")
        return paper
