from datetime import datetime
from typing import Any

from sqlalchemy import Select, or_


def apply_common_filters(
    *,
    base_query: Select[Any],
    model: type[Any],
    created_since: datetime | None,
    created_until: datetime | None,
    modified_since: datetime | None,
    modified_until: datetime | None,
) -> Select[Any]:
    """Apply OParl 1.1 list filters shared by external list endpoints."""
    query = base_query

    if created_since is not None:
        query = query.where(model.created >= created_since)
    if created_until is not None:
        query = query.where(model.created <= created_until)
    if modified_since is not None:
        query = query.where(model.modified >= modified_since)
    if modified_until is not None:
        query = query.where(model.modified <= modified_until)

    # OParl sync semantics: deleted objects are relevant when modified_since is used.
    if modified_since is None:
        query = query.where(or_(model.deleted.is_(None), model.deleted.is_(False)))

    return query
