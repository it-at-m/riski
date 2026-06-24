"""Extractor for gremium memberships - runs after persons and organizations are in DB."""

import httpx
import stamina
from logging import Logger
from config.config import Config, get_config
from core.model.data_models import Organization, OrganizationClassificationEnum, OrganizationTypeEnum
from sqlmodel import Session, select
from core.db.db import get_session

from src.parser.gremium_organization_parser import GremiumOrganizationParser
from src.logtools import getLogger, context_log_url


config: Config = get_config()


class GremiumMembershipExtractor:
    """Extract and link memberships from gremium organization detail pages.

    This must run AFTER CityCouncilMemberExtractor, BAMemberExtractor, and
    the gremium organization extractors, so that Person and Organization
    records are already in the database.
    """

    logger: Logger

    def __init__(
        self,
        classification: OrganizationClassificationEnum,
        org_type: OrganizationTypeEnum | None = None,
    ) -> None:
        self.logger = getLogger()
        self.parser = GremiumOrganizationParser(classification, org_type)
        self.classification = classification
        self.client = httpx.Client(timeout=config.request_timeout, follow_redirects=True)

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _fetch_detail_page(self, url: str) -> str:
        """Fetch a gremium detail page with members tab and high item limit."""
        with context_log_url(url):
            self.logger.debug(f"Fetching {url}")
            # Add tab parameter if not present
            if "tab=" not in url:
                url = url + ("&" if "?" in url else "?") + "tab=mitgliederaktuell"

            # Try with high item limit to get all members in one request
            # Many pagination systems use itemsperpage or similar parameter
            test_urls = [
                url + ("&" if "?" in url else "?") + "itemsperpage=100" if "itemsperpage=" not in url else url,
                url,  # Fallback to original URL
            ]

            for test_url in test_urls:
                try:
                    self.logger.debug(f"Trying {test_url}")
                    response = self.client.get(test_url, follow_redirects=True)
                    response.raise_for_status()
                    return response.text
                except Exception as e:
                    self.logger.debug(f"Failed to fetch {test_url}: {e!r}")
                    continue

            # If all failed, raise the last error
            raise httpx.HTTPError(f"Could not fetch {url}")

    def _get_organization_urls(self) -> list[str]:
        """Get all organization URLs from database matching this extractor's classification."""
        session = get_session()
        try:
            classification_value = self.classification.value
            stmt = select(Organization).where(Organization.classification == classification_value)
            organizations = session.exec(stmt).all()
            urls = [org.id for org in organizations if org.id]
            self.logger.info(f"Found {len(urls)} organizations with classification '{classification_value}'")
            return urls
        finally:
            session.close()

    def run(self) -> None:
        """Extract memberships from all organizations of this classification."""
        try:
            org_urls = self._get_organization_urls()

            if not org_urls:
                self.logger.warning("No organizations found to extract memberships from")
                return

            processed = 0
            failed = 0

            for org_url in org_urls:
                with context_log_url(org_url):
                    try:
                        self.logger.debug(f"Fetching detail page for {org_url}")
                        html = self._fetch_detail_page(org_url)
                        self.logger.debug(f"Extracting memberships from {org_url}")
                        self.parser.extract_memberships(org_url, html)
                        processed += 1
                        self.logger.debug(f"Successfully processed {org_url}")
                    except Exception as e:
                        self.logger.error(f"Error extracting memberships from {org_url}: {e!r}")
                        failed += 1

            self.logger.info(f"Membership extraction complete: {processed} processed, {failed} failed")

        except Exception as e:
            self.logger.exception(f"Error in membership extraction: {e!r}")


class StRFactionMembershipExtractor(GremiumMembershipExtractor):
    """Extract memberships from City Council (StR) factions."""

    def __init__(self) -> None:
        super().__init__(
            OrganizationClassificationEnum.FACTION,
            OrganizationTypeEnum.FACTION,
        )


class StRCommitteeMembershipExtractor(GremiumMembershipExtractor):
    """Extract memberships from City Council (StR) committees."""

    def __init__(self) -> None:
        super().__init__(
            OrganizationClassificationEnum.COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )


class BACommitteeMembershipExtractor(GremiumMembershipExtractor):
    """Extract memberships from District Committee (BA) bodies."""

    def __init__(self) -> None:
        super().__init__(
            OrganizationClassificationEnum.DISTRICT_COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )
