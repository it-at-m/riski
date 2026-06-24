"""Read-only database access for the OParl API: get-by-id and paginated,
time-filtered lists."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select


@dataclass
class TimeFilters:
    """OParl external-list time filters (all optional)."""

    created_since: datetime | None = None
    created_until: datetime | None = None
    modified_since: datetime | None = None
    modified_until: datetime | None = None


def get_by_id(session: Session, model: type, db_id: uuid.UUID):
    """Fetch a single object by primary key, or None."""
    return session.get(model, db_id)


def _apply_filters(stmt, model: type, filters: TimeFilters | None):
    if not filters:
        return stmt
    if filters.created_since is not None:
        stmt = stmt.where(model.created >= filters.created_since)
    if filters.created_until is not None:
        stmt = stmt.where(model.created <= filters.created_until)
    if filters.modified_since is not None:
        stmt = stmt.where(model.modified >= filters.modified_since)
    if filters.modified_until is not None:
        stmt = stmt.where(model.modified <= filters.modified_until)
    return stmt


def list_objects(
    session: Session,
    model: type,
    page: int,
    page_size: int,
    filters: TimeFilters | None = None,
) -> tuple[list, int]:
    """Return (items, total) for a paginated list of ``model`` objects.

    ``page`` is 1-based. Results are ordered by ``created`` for stable paging.
    """
    count_stmt = _apply_filters(select(func.count()).select_from(model), model, filters)
    total = session.exec(count_stmt).one()

    stmt = _apply_filters(select(model), model, filters)
    stmt = stmt.order_by(model.created).offset((page - 1) * page_size).limit(page_size)
    items = list(session.exec(stmt).all())
    return items, total
