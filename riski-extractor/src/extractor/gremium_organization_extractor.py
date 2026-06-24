"""Extractors for city and district council bodies (gremium = committees, factions, etc).

All gremium overview pages live under /gremium and use a consistent detail URL scheme
(/gremium/detail/<id>), but they differ in their filters and iteration approach. The detail
pages and parsing are shared.
"""

from config.config import Config, get_config
from core.model.data_models import Organization, OrganizationClassificationEnum, OrganizationTypeEnum

from src.extractor.base_extractor import BaseExtractor
from src.parser.gremium_organization_parser import GremiumOrganizationParser

config: Config = get_config()


class GremiumOrganizationExtractor(BaseExtractor[Organization]):
    """Base for gremium-sourced organizations (factions, committees, districts)."""

    def __init__(
        self,
        base_path: str,
        classification: OrganizationClassificationEnum,
        org_type: OrganizationTypeEnum | None = None,
    ) -> None:
        super().__init__(
            str(config.base_url) + "/gremium",
            base_path,
            GremiumOrganizationParser(classification, org_type),
            "-2.0-color_container-list-card-cardheader-itemsperpage_dropdown_top",
            "color_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = f"{base_path}?0-1.-form"

    def _extract_links(self, html: str) -> list[str]:
        """Gremium overview pages use headline-link with relative ../detail/<id>."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links = [f"{self.base_url}/{a['href'].lstrip('../')}" for a in soup.select("a.headline-link[href]") if "/detail/" in a["href"]]
        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        return links


class StRFactionExtractor(GremiumOrganizationExtractor):
    """Stadtrat (city council) factions and groupings."""

    def __init__(self) -> None:
        super().__init__(
            "/strfraktion/uebersicht",
            OrganizationClassificationEnum.FACTION,
            OrganizationTypeEnum.FACTION,
        )


class StRCommitteeExtractor(GremiumOrganizationExtractor):
    """Stadtrat (city council) committees."""

    def __init__(self) -> None:
        super().__init__(
            "/strausschuss/uebersicht",
            OrganizationClassificationEnum.COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )


class BACommitteeExtractor(GremiumOrganizationExtractor):
    """Bezirksausschuss (district committee) bodies."""

    def __init__(self) -> None:
        super().__init__(
            "/bezirksausschuss/uebersicht",
            OrganizationClassificationEnum.DISTRICT_COMMITTEE,
            OrganizationTypeEnum.COMMITTEE,
        )
