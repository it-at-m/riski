from config.config import Config, get_config

from src.data_models import Person
from src.extractor.base_extractor import BaseExtractor
from src.parser.person_parser import PersonParser

config: Config = get_config()


class CityCouncilMemberExtractor(BaseExtractor[Person]):
    """
    Extractor for the city council member on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/person",
            "/strmitglieder",
            PersonParser(),
            "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top",
            "list_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "?0-1.-form"
        # TODO: unused!?
        self.detail_path = "/detail"
