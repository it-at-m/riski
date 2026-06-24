"""Parser for committee/faction organizations from /gremium/detail/<id> pages."""

import re

from bs4 import BeautifulSoup
from core.db.db_access import create_membership, get_or_create_legislative_term
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

    def _extract_dates_from_parent(self, element) -> tuple[str | None, str | None]:
        """
        Extract start and end dates from the parent row context.
        Dates are typically in format "01.01.2026" or "01.01.2026 - 31.12.2032".
        """
        start_date = None
        end_date = None

        try:
            parent = element.parent
            if not parent:
                return start_date, end_date

            parent_text = parent.get_text(strip=True)

            # Look for date patterns like "01.01.2026" or "01.01.2026 - 31.12.2032"
            dates = re.findall(r"(\d{1,2}\.\d{1,2}\.\d{4})", parent_text)

            if dates:
                start_date = self._german_date_to_iso(dates[0])
                if len(dates) > 1:
                    end_date = self._german_date_to_iso(dates[1])
        except Exception as e:
            self.logger.debug(f"Could not extract dates from context: {e!r}")

        return start_date, end_date

    def _german_date_to_iso(self, date_str: str) -> str | None:
        """Convert German date format (dd.mm.yyyy) to ISO format (yyyy-mm-dd)."""
        try:
            match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception as e:
            self.logger.debug(f"Could not convert date {date_str}: {e!r}")
        return None

    def _extract_role_from_context(self, element) -> str:
        """
        Extract role from the element's context.
        Checks parent and surrounding text for role keywords.
        """
        role = "Mitglied"

        try:
            # Check parent row text
            parent = element.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True).lower()

                if "vorsitzende" in parent_text or "vorsitz" in parent_text:
                    role = "Vorsitz"
                elif "stellvertreter" in parent_text or "stellvertretende" in parent_text:
                    role = "Stellvertreter"
                elif "schriftführer" in parent_text:
                    role = "Schriftführer"
                elif "kassenwart" in parent_text or "kassenverwalter" in parent_text:
                    role = "Kassenwart"
                elif "obfrau" in parent_text or "obmann" in parent_text:
                    role = "Obmann"

                # Also check parent's parent (row container)
                grandparent = parent.parent
                if grandparent and role == "Mitglied":
                    gp_text = grandparent.get_text(" ", strip=True).lower()
                    if "vorsitzende" in gp_text or "vorsitz" in gp_text:
                        role = "Vorsitz"
                    elif "stellvertreter" in gp_text:
                        role = "Stellvertreter"
        except Exception as e:
            self.logger.debug(f"Could not extract role: {e!r}")

        return role

    def _resolve_person_url(self, href: str, org_url: str) -> str | None:
        """Resolve a person href (relative or absolute) to a full URL.

        Handles:
        - Absolute paths: /person/detail/123 -> https://risi.muenchen.de/person/detail/123
        - Relative paths: ../../person/detail/123 -> resolve relative to org_url
        - Query parameters: strip ?tab=mitgliedschaften
        """
        if not href:
            return None

        # Remove query parameters and session ids
        href = href.split("?")[0].split(";")[0]

        # Handle absolute paths (start with /)
        if href.startswith("/"):
            return f"https://risi.muenchen.de{href}"

        # Handle relative paths (../../person/detail/...)
        if href.startswith(".."):
            from urllib.parse import urljoin

            return urljoin(org_url, href)

        # Already absolute URL
        if href.startswith("http"):
            return href

        return None

    def _extract_members_and_create_memberships(self, soup: BeautifulSoup, org_url: str) -> None:
        """Extract member list from gremium detail page and create Membership records."""
        try:
            # Find all person detail links - match various patterns:
            # - /person/detail/XXX
            # - ../../person/detail/XXX
            # - person/detail/XXX
            member_links = soup.find_all("a", href=re.compile(r"person/detail/", re.IGNORECASE))

            if not member_links:
                self.logger.info(f"No member links found on page for {org_url}")
                return

            self.logger.info(f"Found {len(member_links)} potential member links for {org_url}")

            # Track processed members to avoid duplicates
            processed = set()
            created_count = 0
            failed_count = 0
            skipped_duplicate = 0

            for link in member_links:
                try:
                    person_text = link.get_text(strip=True)
                    person_href = link.get("href")

                    if not person_href or not person_text:
                        self.logger.debug("Skipped link with empty href or text")
                        continue

                    # Resolve person URL (handles relative and absolute paths)
                    person_url = self._resolve_person_url(person_href, org_url)
                    if not person_url:
                        self.logger.debug(f"Could not resolve person URL from {person_href}")
                        continue

                    # Skip if already processed
                    if person_url in processed:
                        skipped_duplicate += 1
                        continue
                    processed.add(person_url)

                    # Extract role with enhanced detection
                    role = self._extract_role_from_context(link)

                    # Extract dates from parent context
                    start_date, end_date = self._extract_dates_from_parent(link)

                    # Create membership
                    membership = create_membership(
                        person_id=person_url,
                        organization_id=org_url,
                        role=role,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    if membership:
                        created_count += 1
                        self.logger.debug(f"Created membership: {person_text} ({role})")
                    else:
                        failed_count += 1
                        self.logger.warning(f"Failed to create membership for {person_text} (Person or Org not found)")

                except Exception as e:
                    failed_count += 1
                    self.logger.warning(f"Error processing member {person_text}: {e!r}")

            self.logger.info(
                f"Membership extraction complete: {created_count} created, {failed_count} failed, {skipped_duplicate} duplicates skipped (total unique: {len(processed)})"
            )

        except Exception as e:
            self.logger.error(f"Error extracting members: {e!r}")

    def extract_memberships(self, url: str, html: str) -> None:
        """Extract and create memberships from a gremium detail page.

        This is called separately from parse() to ensure Person and Organization
        records are already in the database.
        """
        soup = BeautifulSoup(html, "html.parser")
        self._extract_members_and_create_memberships(soup, url)

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
