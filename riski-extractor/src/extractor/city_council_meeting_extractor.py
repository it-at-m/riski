from config.config import Config, get_config
from core.model.data_models import Meeting

from src.extractor.base_extractor import BaseExtractor
from src.parser.city_council_meeting_parser import CityCouncilMeetingParser

config: Config = get_config()


class CityCouncilMeetingExtractor(BaseExtractor[Meeting]):
    """
    Extractor for Meetings on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/sitzung",
            "/uebersicht",
            CityCouncilMeetingParser(),
            "-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top",
            "list_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "/uebersicht?0-1.-form"
        self.extend_filter_data = {"containerBereichDropDown:bereich": "2"}
