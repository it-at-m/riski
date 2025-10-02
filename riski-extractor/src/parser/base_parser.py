from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from bs4 import BeautifulSoup

T = TypeVar("T")


class BaseParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, link: str, content: str) -> T:
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
