from bs4 import BeautifulSoup
from config.config import Config, get_config
from core.model.data_models import Paper, PaperTypeEnum

from src.extractor.base_extractor import BaseExtractor
from src.parser.bezirksausschuss_paper_parser import BezirksausschussPaperParser

config: Config = get_config()

# Wicket identifiers are identical for all overview pages under /antrag/ba/.
_RESULTS_PER_PAGE_URL = "-2.0-color_container-list-card-cardheader-itemsperpage_dropdown_top"
_RESULTS_PER_PAGE_KEY = "color_container:list:card:cardheader:itemsperpage_dropdown_top"


class BezirksausschussPaperExtractor(BaseExtractor[Paper]):
    """
    Base extractor for papers in the Bezirksausschuss section (``/antrag/ba/``).

    Concrete subclasses only differ in their overview page and the resulting
    OParl paper type. The detail pages live under ``/antrag/detail/<id>``,
    so the relative ``../detail/...`` links are resolved against ``/antrag``.
    """

    def __init__(self, overview_path: str, paper_type: PaperTypeEnum) -> None:
        super().__init__(
            str(config.base_url) + "/antrag/ba",
            f"/{overview_path}",
            BezirksausschussPaperParser(paper_type),
            _RESULTS_PER_PAGE_URL,
            _RESULTS_PER_PAGE_KEY,
        )
        self.filter_url = f"/{overview_path}?0-1.-filtersection_container-form"

    def _extract_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        base_url_without_suffix = self.base_url.removesuffix("/ba")
        links = [
            f"{base_url_without_suffix}/{a['href'].lstrip('../')}"
            for a in soup.select("a.headline-link[href]")
            if a["href"].startswith("../detail/")
        ]
        self.logger.info(f"Extracted {len(links)} links to parsable objects from page.")
        return links


class BAMotionExtractor(BezirksausschussPaperExtractor):
    """Bezirksausschuss-Anträge (district committee proposals)."""

    def __init__(self) -> None:
        super().__init__("baantraguebersicht", PaperTypeEnum.DISTRICT_COMMITTEE_PROPOSAL)


class BVRecommendationExtractor(BezirksausschussPaperExtractor):
    """Bürgerversammlungs-Empfehlungen (citizens' assembly recommendations)."""

    def __init__(self) -> None:
        super().__init__("bvempfehlunguebersicht", PaperTypeEnum.CITIZENS_ASSEMBLY_RECOMMENDATION)


class BVRequestExtractor(BezirksausschussPaperExtractor):
    """Bürgerversammlungs-Anfragen (citizens' assembly requests)."""

    def __init__(self) -> None:
        super().__init__("bvanfrageuebersicht", PaperTypeEnum.CITIZENS_ASSEMBLY_REQUEST)
