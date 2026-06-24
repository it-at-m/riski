"""Parser for committee/faction organizations from /gremium/detail/<id> pages."""

import re

from bs4 import BeautifulSoup
from core.db.db_access import get_or_create_legislative_term
from core.model.data_models import Organization, OrganizationClassificationEnum, OrganizationTypeEnum

from src.parser.base_parser import BaseParser


class GremiumOrganizationParser(BaseParser[Organization]):
    """
    Parse Gremium (committee/faction) organizations from their detail pages.

    All gremium detail pages share a consistent structure: title, optional shortname
    (Kürzel) and classification/type (Typ) in key-value rows, plus optional address/contact info.
    """

    def __init__(
        self,
        classification: OrganizationClassificationEnum,
        org_type: OrganizationTypeEnum | None = None,
    ) -> None:
        super().__init__()
        self.classification = classification
        self.org_type = org_type
        self.logger.info(f"Gremium parser initialized for {classification}.")

    def _extract_seats_from_title(self, title: str) -> int | None:
        """Extract seat count from titles like 'CSU-Stadtratsfraktion (19 Sitze)'."""
        match = re.search(r"\((\d+)\s+Sitze\)", title)
        return int(match.group(1)) if match else None

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

    def parse(self, url: str, html: str) -> Organization:
        soup = BeautifulSoup(html, "html.parser")

        # --- title (name) ---
        title = self._get_title(soup, self.logger)
        if not title:
            self.logger.warning("No title found")
            return None

        # --- shortname (Kürzel) and type from key-value rows ---
        short_name = self._kv_value("Kürzel:", soup)
        type_str = self._kv_value("Typ:", soup)

        # --- legislative term (Wahlperiode) ---
        wahlperiode = self._kv_value("Wahlperiode:", soup)
        self._ensure_legislative_term(wahlperiode)

        # --- organization type: use supplied type or infer from type_str if available ---
        org_type = self.org_type
        if org_type is None and type_str:
            if "fraktion" in type_str.lower():
                org_type = OrganizationTypeEnum.FACTION
            elif "ausschuss" in type_str.lower():
                org_type = OrganizationTypeEnum.COMMITTEE
            elif "bezirk" in type_str.lower() or "district" in type_str.lower():
                org_type = OrganizationTypeEnum.COUNCIL

        # --- assemble organization ---
        org = Organization(
            id=url,
            name=title,
            shortName=short_name,
            classification=self.classification,
            organizationType=org_type,
            inactive=False,
            web=url,
            deleted=False,
        )
        # Initialize relationships to avoid DetachedInstanceError
        org.membership = []
        org.post = []
        org.subOrganizations = []
        org.keywords = []
        org.papers = []
        org.directed_papers = []
        org.meetings = []

        self.logger.debug(f"Parsed organization {title} ({org_type}) from {url}")
        return org
