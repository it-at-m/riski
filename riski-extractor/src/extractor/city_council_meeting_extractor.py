import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Meeting
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

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": config.end_date, "status": "", "containerBereichDropDown:bereich": "2"}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")
