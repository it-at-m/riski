from config.config import Config, get_config
from core.model.data_models import Paper

from src.extractor.base_extractor import BaseExtractor
from src.parser.city_council_meeting_template_parser import CityCouncilMeetingTemplateParser

config: Config = get_config()


class CityCouncilMeetingTemplateExtractor(BaseExtractor[Paper]):
    """
    Extractor for the City Council Meeting Templates on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/sitzungsvorlage",
            "/uebersicht",
            CityCouncilMeetingTemplateParser(),
            "-2.0-color_container-list-card-cardheader-itemsperpage_dropdown_top",
            "color_container:list:card:cardheader:itemsperpage_dropdown_top",
        )
        self.filter_url = "/uebersicht?0-1.-filtersection_container-form"
