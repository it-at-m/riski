import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Person
from src.extractor.base_extractor import BaseExtractor
from src.parser.person_parser import PersonParser

config: Config = get_config()


class HeadOfDepartmentExtractor(BaseExtractor[Person]):
    """
    Extractor for the Heads of Departments on the RIS website
    """

    def __init__(self) -> None:
        super().__init__(
            str(config.base_url) + "/person",
            "/referenten",
            PersonParser(),
            "?0-1.0-list-card-cardheader-itemsperpage_dropdown_top",
            "list:card:cardheader:itemsperpage_dropdown_top",
        )

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        return self.base_path
