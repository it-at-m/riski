import httpx
import stamina
from config.config import Config, get_config

from src.data_models import Person
from src.extractor.base_extractor import BaseExtractor
from src.parser.head_of_department_parser import HeadOfDepartmentParser

config: Config = get_config()


class HeadOfDepartmentExtractor(BaseExtractor[Person]):
    """
    Extractor for the Heads of Departments on the RIS website
    """

    def __init__(self) -> None:
        BaseExtractor.__init__(self, str(config.base_url) + "/person", "/referenten", HeadOfDepartmentParser())

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _set_results_per_page(self, path: str) -> str:
        url = self.base_url + self.base_path + "?0-1.0-list-card-cardheader-itemsperpage_dropdown_top"
        data = {"list:card:cardheader:itemsperpage_dropdown_top": 3}  # 3 is the third entry in a dropdown menu representing the count 100
        response = self.client.post(url=url, data=data)
        assert response.is_redirect  # When sending a filter request the RIS always returns a redirect to the url with the filtered results
        return response.headers.get("Location")

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def _filter(self) -> str:
        pass
