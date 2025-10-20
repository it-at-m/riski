import locale
import platform
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from bs4 import BeautifulSoup

from src.data_models import PaperSubtypeEnum
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
    def parse(self, link: str, content: str) -> T | None:
        pass

    def _kv_value(self, key_label: str, soup: BeautifulSoup) -> str | None:
        """Extracts values from key-value container rows by label."""
        for row in soup.select(".keyvalue-container .keyvalue-row"):
            key = row.select_one(".keyvalue-key")
            value = row.select_one(".keyvalue-value")
            if key and value and key.get_text(strip=True).rstrip(":") == key_label.rstrip(":"):
                return value.get_text(" ", strip=True)
        return None

    def _get_title(self, soup, logger=None):
        """Extracts the title text from a BeautifulSoup object."""
        title_tag = soup.select_one("h1.page-title")
        if not title_tag:
            if logger:
                logger.warning("No title found, skipping.")
            return None

        title_text = title_tag.get_text(strip=True, separator=" ")
        return title_text

    def _get_paper_subtype_enum(self, paper_subtype_string: str) -> PaperSubtypeEnum | None:
        if not paper_subtype_string:
            return None
        s = paper_subtype_string.strip()
        norm = s.casefold()
        if "beschlussvorlage" in norm and "sb" in norm and "vb" in norm:
            return PaperSubtypeEnum.RESOLUTION_TEMPLATE_SB_VB
        if "beschlussvorlage" in norm and "sb" in norm:
            return PaperSubtypeEnum.RESOLUTION_TEMPLATE_SB
        if "beschlussvorlage" in norm and "vb" in norm:
            return PaperSubtypeEnum.RESOLUTION_TEMPLATE_VB
        # exact value match via Enum casting
        try:
            return PaperSubtypeEnum(s)
        except ValueError:
            self.logger.warning(f"Unknown PaperSubtypeEnum value: '{s}'")
            return None
