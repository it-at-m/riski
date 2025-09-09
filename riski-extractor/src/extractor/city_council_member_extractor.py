import httpx
import stamina
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
        self.detail_path = "/detail"

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        filter_url = self._get_sanitized_url(self.base_path) + "?0-1.-form"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"von": config.start_date, "bis": "", "fraktion": "", "nachname": ""}
        response = self.client.post(url=filter_url, headers=headers, data=data)

        if response.is_redirect:
            redirect_url = response.headers.get("Location")
            self.logger.debug(f"Filter Redirect URL: {redirect_url}")
            return redirect_url
        else:
            response.raise_for_status()
