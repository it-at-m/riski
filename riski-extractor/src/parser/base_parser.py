from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, link: str, content: str) -> T:
        pass
