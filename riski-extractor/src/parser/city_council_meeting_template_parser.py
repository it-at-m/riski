from logging import Logger

from src.data_models import Paper
from src.logtools import getLogger
from src.parser.base_parser import BaseParser

DATE_FORMAT = "%d.%m.%Y"
KILOBYTE = 1024


class CityCouncilMeetingTemplateParser(BaseParser[Paper]):
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.logger.info("City Council Meeting Template Parser initialized.")

    def parse(self, url: str, html: str) -> Paper | None:
        return None
