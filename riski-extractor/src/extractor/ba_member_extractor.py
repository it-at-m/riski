from config.config import Config, get_config
from core.model.data_models import Person

from src.extractor.base_extractor import BaseExtractor
from src.parser.person_parser import PersonParser

config: Config = get_config()


class BAMemberExtractor(BaseExtractor[Person]):
    """
    Extractor for the district committee (Bezirksausschuss) members on the RIS website.

    Mirrors the city council member extractor; only the overview page differs.
    Person detail pages and parsing are identical, so the PersonParser is reused.
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/person",
            "/bamitglieder",
            PersonParser(),
            "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top",
            "list_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "?0-1.-form"
