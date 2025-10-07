import locale
import platform
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.logtools import getLogger

T = TypeVar("T")


class BaseParser(ABC, Generic[T]):
    def __init__(self) -> None:
        self.logger = getLogger()
        if platform.system() == "Windows":
            # For Windows, use the specific code page that works
            locale.setlocale(locale.LC_TIME, "German_Germany.1252")
        else:
            try:
                locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
                self.logger.info("German locale 'de_DE.utf8' applied.")
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, "de_DE")
                    self.logger.info("German locale 'de_DE' fallback applied.")
                except locale.Error:
                    self.logger.warning("Locale 'de_DE' not available. Date parsing may fail.")

    @abstractmethod
    def parse(self, link: str, content: str) -> T:
        pass
