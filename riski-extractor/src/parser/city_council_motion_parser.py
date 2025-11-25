import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_models import File, Keyword, Organization, Paper, PaperTypeEnum, Person
from src.db.db_access import (
    get_or_insert_object_to_database,
    request_object_by_name,
    request_paper_by_reference,
    request_person_by_full_name,
    update_or_insert_objects_to_database,
)
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

    def _extract_meeting_template_reference(self, text: str) -> str | None:
        # Regex: digits-digits / V digits
        match = re.search(r"\d+-\d+\s*/\s*V\s*\d+", text)
        return match.group(0) if match else None

    def _detect_paper_type(self, text: str | None) -> str:
        """Detects whether it is a city council motion or a city council inquiry."""
        if not text:
            return "StR-Antrag/Anfrage"
        text_lower = text.lower()
        if "str-anfrage" in text_lower:
            return PaperTypeEnum.COUNCIL_REQUEST
        elif "str-antrag" in text_lower:
            return PaperTypeEnum.COUNCIL_PROPOSAL
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
        paper_type = self._detect_paper_type(title)
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
        paper_subtype = self._get_paper_subtype_enum(paper_subtype_string) if paper_subtype_string else None

        # --- originators (persons + orgs) ---
        originator_text = self._kv_value("Gestellt von:", soup)
        originator_persons, originator_orgs = self._resolve_originators(originator_text)
        initiative_text = self._kv_value("Initiative:", soup)
        if initiative_text:
            initiative_persons, initiative_orgs = self._resolve_originators(initiative_text)
            unique_persons = {p.id: p for p in originator_persons}  # dict: id → Objekt
            for p in initiative_persons:
                unique_persons.setdefault(p.id, p)
            originator_persons = list(unique_persons.values())

            unique_orgs = {o.id: o for o in originator_orgs}
            for o in initiative_orgs:
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

            if fname == "Beschluss.pdf":
                fname = f"Beschluss zu {title}"
            fname = fname.removesuffix(".pdf")

            file = get_or_insert_object_to_database(File(id=full_url, name=fname, fileName=fname, accessUrl=full_url, downloadUrl=full_url))
            # This update should only occur on the first extraction run a file is found.
            # It is first found via the meeting template
            file.name = fname
            update_or_insert_objects_to_database([file])

            auxiliary_files.append(file)

        # Meeting Templates
        related_paper = []
        result = soup.select_one('section.card[aria-labelledby="sectionheader-ergebnisse"] div.list-group')
        sv_links = result.find_all("a", href=True) if result else []
        for sv_link in sv_links:
            # Suche nach dem Link zur Sitzungsvorlage
            if sv_link and "Sitzungsvorlage" in sv_link.text:
                sv_reference = self._extract_meeting_template_reference(sv_link.text)
                sv = request_paper_by_reference(sv_reference, self.logger)
                related_paper.append(sv)
        paper_dict = {p.id: p for p in related_paper if p is not None}  # dict: id → Objekt
        related_paper = list(paper for paper in paper_dict.values())

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
            paper_type=paper_type,
            paper_subtype=paper_subtype,
            date=date,
            originator_persons=originator_persons,
            originator_orgs=originator_orgs,
            reference=reference,
            related_papers=related_paper,
        )

        self.logger.debug(f"Parsed {paper_type} {reference} from {url}")
        return paper
