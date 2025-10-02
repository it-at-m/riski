from bs4.element import Tag
from config.config import Config, get_config

from src.data_models import Organization
from src.extractor.base_extractor import BaseExtractor
from src.parser.city_council_faction_parser import CityCouncilFactionParser

config: Config = get_config()


class CityCouncilFactionExtractor(BaseExtractor[Organization]):
    """
    Extractor for the city council factions on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "",
            "/erweitertesuche?objekt=FRAKTION",
            CityCouncilFactionParser(),
            "-2.0-trefferlisteContainer-trefferliste-card-cardheader-itemsperpage_dropdown_top",
            "trefferlisteContainer:trefferliste:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "&0-1.-suchkriterienContainer-suchkriterien-form"
        self.additional_link_filter = self.is_city_council_faction

    def is_city_council_faction(self, element: Tag) -> bool:
        parent = element.find_parent(class_="list-group-item")
        if parent:
            return parent.find(string="Stadtratsarbeit") is not None

        return False
