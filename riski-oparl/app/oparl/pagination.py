"""OParl external-list pagination envelope."""

import math
from typing import Any


def make_list_envelope(data: list[Any], total: int, page: int, page_size: int, list_url: str) -> dict[str, Any]:
    """Build an OParl-compliant paginated list response.

    Contains the ``data`` array, a ``pagination`` object and ``links`` with
    first/prev/next/last as required by the OParl specification.
    """
    total_pages = max(1, math.ceil(total / page_size)) if page_size else 1

    def page_url(p: int) -> str:
        return f"{list_url}?page={p}"

    links: dict[str, str] = {
        "first": page_url(1),
        "last": page_url(total_pages),
    }
    if page > 1:
        links["prev"] = page_url(page - 1)
    if page < total_pages:
        links["next"] = page_url(page + 1)

    return {
        "data": data,
        "pagination": {
            "totalElements": total,
            "elementsPerPage": page_size,
            "currentPage": page,
            "totalPages": total_pages,
        },
        "links": links,
    }
