from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationInfo(BaseModel):
    """OParl list pagination metadata."""

    totalElements: int | None = Field(default=None)
    elementsPerPage: int | None = Field(default=None)
    currentPage: int | None = Field(default=None)
    totalPages: int | None = Field(default=None)


class PaginationLinks(BaseModel):
    """OParl list pagination links."""

    first: str | None = Field(default=None)
    last: str | None = Field(default=None)
    prev: str | None = Field(default=None)
    next: str | None = Field(default=None)
    self: str | None = Field(default=None)
    web: str | None = Field(default=None)


class OParlListResponse(BaseModel, Generic[T]):
    """Generic OParl external list response envelope."""

    data: list[T]
    pagination: PaginationInfo
    links: PaginationLinks
