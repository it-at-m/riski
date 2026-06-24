"""Extractor for gremium organizational hierarchies (sub-organizations)."""

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


class GremiumHierarchyExtractor:
    """Extract and link sub-organization hierarchies from gremium detail pages.

    This must run AFTER all gremium organizations are in the database,
    so that both parent and child organizations exist for linking.
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
        """Fetch a gremium detail page."""
        with context_log_url(url):
            self.logger.debug(f"Fetching {url}")
            response = self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text

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
        """Extract hierarchies from all organizations of this classification."""
        try:
            org_urls = self._get_organization_urls()

            if not org_urls:
                self.logger.warning("No organizations found to extract hierarchies from")
                return

            processed = 0
            failed = 0

            for org_url in org_urls:
                with context_log_url(org_url):
                    try:
                        self.logger.debug(f"Fetching detail page for {org_url}")
                        html = self._fetch_detail_page(org_url)
                        self.logger.debug(f"Extracting sub-organizations from {org_url}")
                        self.parser.extract_sub_organizations(org_url, html)
                        processed += 1
                        self.logger.debug(f"Successfully processed {org_url}")
                    except Exception as e:
                        self.logger.error(f"Error extracting hierarchies from {org_url}: {e!r}")
                        failed += 1

            self.logger.info(f"Hierarchy extraction complete: {processed} processed, {failed} failed")

        except Exception as e:
            self.logger.exception(f"Error in hierarchy extraction: {e!r}")


class StRCommitteeHierarchyExtractor(GremiumHierarchyExtractor):
    """Extract hierarchies from City Council (StR) committees."""

    def __init__(self) -> None:
        super().__init__(
            OrganizationClassificationEnum.COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )


class BACommitteeHierarchyExtractor(GremiumHierarchyExtractor):
    """Extract hierarchies from District Committee (BA) bodies."""

    def __init__(self) -> None:
        super().__init__(
            OrganizationClassificationEnum.DISTRICT_COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )
