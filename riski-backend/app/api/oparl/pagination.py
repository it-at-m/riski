import math
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.settings import BackendSettings
from app.models.oparl import OParlListResponse, PaginationInfo, PaginationLinks
from fastapi import Request
from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


def _replace_query_params(request: Request, **params: Any) -> str:
    filtered = {k: v for k, v in params.items() if v is not None}
    return str(request.url.replace_query_params(**filtered))


async def build_paginated_response(
    *,
    request: Request,
    session: AsyncSession,
    base_query: Select[Any],
    count_from: type[Any],
    serializer: Callable[[Any], T],
    page: int,
    limit: int,
    settings: BackendSettings,
) -> OParlListResponse[T]:
    """Execute a paginated query and return an OParl list envelope."""
    page_size = min(limit, settings.oparl_page_size_max)
    offset = (page - 1) * page_size

    count_stmt = base_query.order_by(None).limit(None).offset(None).with_only_columns(func.count(), maintain_column_froms=True)
    total_elements = int((await session.execute(count_stmt)).scalar_one())

    stmt = base_query.offset(offset).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()

    total_pages = max(1, math.ceil(total_elements / page_size)) if total_elements > 0 else 1
    current_page = min(page, total_pages)

    base_params = dict(request.query_params)
    base_params["limit"] = page_size
    base_params["page"] = current_page

    first_link = _replace_query_params(request, **{**base_params, "page": 1})
    last_link = _replace_query_params(request, **{**base_params, "page": total_pages})
    self_link = _replace_query_params(request, **base_params)
    prev_link = _replace_query_params(request, **{**base_params, "page": current_page - 1}) if current_page > 1 else None
    next_link = _replace_query_params(request, **{**base_params, "page": current_page + 1}) if current_page < total_pages else None

    pagination = PaginationInfo(
        totalElements=total_elements,
        elementsPerPage=page_size,
        currentPage=current_page,
        totalPages=total_pages,
    )
    links = PaginationLinks(first=first_link, last=last_link, prev=prev_link, next=next_link, self=self_link, web=self_link)
    return OParlListResponse(data=[serializer(row) for row in rows], pagination=pagination, links=links)
