import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Paper
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

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self.base_url + "/uebersicht?0-1.-filtersection_container-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": config.end_date}
        response = self.client.post(url=filter_url, headers=headers, data=data)
        if not response.is_redirect:  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
            raise httpx.HTTPStatusError(
                "Expected redirect from filter request",
                request=response.request,
                response=response,
            )
        return response.headers.get("Location")
