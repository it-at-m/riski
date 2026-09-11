import asyncio
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from datetime import time as datetime_time
from functools import wraps
from typing import List, Literal, TypeVar, overload

from sqlalchemy import and_, distinct, func, inspect, or_
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Session, select

from core.db.db import get_session
from core.logtools import getLogger
from core.model.data_models import (
    RIS_NAME_OBJECT,
    RIS_PARSED_DB_OBJECT,
    File,
    Keyword,
    LegislativeTerm,
    Organization,
    OrganizationClassificationEnum,
    OrganizationTypeEnum,
    Paper,
    PaperOriginatorOrgLink,
    PaperSubtypeEnum,
    PaperTypeEnum,
    Person,
)

T = TypeVar("T", bound=RIS_PARSED_DB_OBJECT)
N = TypeVar("N", bound=RIS_NAME_OBJECT)
UPDATE_EXCLUDED_FIELDS_BY_CLASS = {
    File: {"content", "size"},
}

logger = getLogger()


def log_execution_time(func):
    """Decorator to log execution time and entrance/exit of a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log entrance
        logger.debug(f"Entering: {func.__name__}")

        start_time = time.time()

        try:
            # call function
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Log exit
            logger.debug(f"Exiting: {func.__name__}")
            logger.debug(f"Execution time for {func.__name__}: {execution_time:.4f} seconds")

        return result

    return wrapper


@contextmanager
def _get_session_ctx():
    """
    Yield a session from `get_session()`.
    Use as: `with _get_session_ctx() as sess:`
    The code that owns the session must own commit/rollback.
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def optional_session(session: Session | None = None):
    if session is not None:
        yield session
    else:
        with _get_session_ctx() as sess:
            yield sess


@log_execution_time
def request_object_by_risid(risid: str, object_type: type[T], session: Session) -> T | None:
    statement = select(object_type).where(object_type.id == risid)
    obj = session.exec(statement).first()
    return obj


@log_execution_time
def request_all(object_type: type[T]) -> List[T]:
    statement = select(object_type)
    with _get_session_ctx() as sess:
        objects = list(sess.exec(statement).all())
        return objects


@overload
def request_object_by_name(name: str, object_type: type[N], session: Session | None = None) -> N | None: ...


@overload
def request_object_by_name(name: str, object_type: type[Keyword], session: Session | None = None) -> Keyword | None: ...


@log_execution_time
def request_object_by_name(name: str, object_type: type[N] | type[Keyword], session: Session | None = None) -> N | Keyword | None:
    with optional_session(session) as sess:
        statement = select(object_type).where(object_type.name == name)
        obj = sess.exec(statement).first()
        return obj


@log_execution_time
def remove_object_by_id(id: str, object_type: type[T]):
    statement = select(object_type).where(object_type.id == id)
    with _get_session_ctx() as session:
        obj = session.exec(statement).first()
        if obj is None:
            logger.warning(f"Object with id '{id}' not found for deletion")
            return
        session.delete(obj)
        session.commit()


@log_execution_time
def insert_and_return_object(obj: RIS_PARSED_DB_OBJECT | Keyword, session: Session | None = None) -> RIS_PARSED_DB_OBJECT | Keyword:
    with optional_session(session) as sess:
        try:
            sess.add(obj)
            if session is None:
                sess.commit()
                sess.refresh(obj)
            return obj
        except Exception:
            if session is None:
                sess.rollback()
            raise


@log_execution_time
def request_person_by_familyName(familyName: str) -> Person | None:
    statement = select(Person).where(Person.familyName == familyName)
    with _get_session_ctx() as sess:
        results = list(sess.exec(statement).all())
        if len(results) > 1:
            logger.warning(f"Multiple Person records found for familyName '{familyName}'. Returning first match.")
        return results[0] if results else None


@log_execution_time
def update_or_insert_objects_to_database(objects: List[T]) -> None:
    total = len(objects)
    logger.debug("update_or_insert_objects_to_database: processing %d objects", total)
    for idx, obj in enumerate(objects, start=1):
        # Each object gets its own session/transaction for fault isolation
        # failures on individual objects won't roll back the entire batch.
        with _get_session_ctx() as sess:
            obj_db = request_object_by_risid(obj.id, type(obj), sess)
            if obj_db:
                logger.debug("updating existing %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                update_object(obj, obj_db, sess)
            else:
                logger.debug("inserting new %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                insert_object_to_database(obj, sess)
            sess.commit()


@log_execution_time
def update_object(obj, obj_db, session: Session) -> None:
    """
    Update a persistent ORM object using PUT semantics.

    The incoming `obj` is treated as the complete desired state:
    - Scalar fields are fully overwritten
    - Relationship collections are replaced wholesale
    - Missing or empty relationships remove existing associations
    - Related rows are NOT deleted unless cascade rules specify it

    Assumptions / guarantees:
    - `obj` is NOT attached to the session
    - `obj_db` IS persistent in the session
    - Related objects may already exist in the database
    - Related objects may be transient or detached
    - Relationship existence / authorization has been validated beforehand

    PUT impact:
    - Missing relationships ⇒ cleared
    - Removed collection items ⇒ disassociated
    - Orphan deletion occurs ONLY if `delete-orphan` is configured
    """
    mapper = inspect(obj_db).mapper
    pk_keys = {col.key for col in mapper.primary_key}
    excluded = UPDATE_EXCLUDED_FIELDS_BY_CLASS.get(type(obj_db), set())

    for attr in mapper.attrs:
        name = attr.key

        # Never overwrite identity or audit fields
        if name in pk_keys or name in {"created", "modified"}:
            continue

        if name in excluded:
            continue

        incoming = getattr(obj, name, None)
        updated_value = None

        # ---------- relationships ----------
        if isinstance(attr, RelationshipProperty):
            if attr.uselist:
                if incoming is None:
                    updated_value = []
                else:
                    updated_items = []
                    for item in incoming:
                        state = inspect(item)

                        if state.detached:
                            item = session.merge(item)
                        elif state.transient:
                            session.add(item)

                        updated_items.append(item)

                    updated_value = updated_items
            else:
                if incoming is None:
                    updated_value = None
                else:
                    state = inspect(incoming)

                    if state.detached:
                        incoming = session.merge(incoming)
                    elif state.transient:
                        session.add(incoming)

                    updated_value = incoming

        # ---------- scalar columns ----------
        else:
            updated_value = incoming

        setattr(obj_db, name, updated_value)


@log_execution_time
def update_file_content(file_id, content, fileName=None):
    with _get_session_ctx() as session:
        file_db = session.get(File, file_id)
        if not file_db:
            return

        file_db.content = content
        file_db.size = len(content)
        if fileName:
            file_db.fileName = fileName
        session.commit()


@log_execution_time
def insert_object_to_database(obj: T, session: Session) -> None:
    session.add(obj)


@log_execution_time
def get_or_insert_object_to_database(obj: RIS_PARSED_DB_OBJECT | Keyword) -> RIS_PARSED_DB_OBJECT | Keyword:
    """
    Retrieves or inserts an object into the database.

    Args:
        obj (T | Keyword): The object to retrieve or insert, identified by 'name' (keyword)
                 or 'id' (for others).

    Returns:
        obj_db: The retrieved or inserted object.
    """
    with _get_session_ctx() as sess:
        logger.debug("get_or_inserting new %s id=%s", type(obj).__name__, getattr(obj, "id", None))
        if isinstance(obj, Keyword):
            obj_db = request_object_by_name(obj.name, type(obj), sess)
        else:
            obj_db = request_object_by_risid(obj.id, type(obj), sess)

        if not obj_db:
            logger.debug("Not found. Inserting new %s id=%s", type(obj).__name__, getattr(obj, "id", None))
            obj_db = insert_and_return_object(obj, sess)
            sess.commit()
    return obj_db


@log_execution_time
def request_paper_by_reference(reference: str) -> None | Paper:
    stmt = select(Paper).where(Paper.reference == reference)
    with _get_session_ctx() as sess:
        results = list(sess.exec(stmt).all())

        if not results:
            logger.warning(f"No paper found for {reference}")
            return None
        elif len(results) > 1:
            logger.warning(f"Multiple papers found for reference '{reference}' — using the first one")

        paper = results[0]
        logger.debug(f"Found paper {reference} in DB (id={paper.id})")
        return paper


@log_execution_time
def request_person_by_full_name(familyName: str, givenName: str) -> Person | None:
    stmt = select(Person).where(Person.familyName == familyName, Person.givenName == givenName)
    with _get_session_ctx() as sess:
        results = list(sess.exec(stmt).all())

        if not results:
            logger.warning(f"No person found for {givenName} {familyName}")
            return None
        elif len(results) > 1:
            logger.warning(f"Multiple persons found for {givenName} {familyName} — using the first one")

        person = results[0]
        logger.debug(f"Found person {givenName} {familyName} in DB (id={person.id})")
        return person


@log_execution_time
def request_batch(model: type[T], offset: int, limit: int) -> List[T]:
    """
    Loads a batch of records for a given model with offset and limit.
    """
    statement = select(model).order_by(model.db_id).offset(offset).limit(limit)
    with _get_session_ctx() as sess:
        return list(sess.exec(statement).all())


@log_execution_time
async def _completed_legislative_term(db_session, query_timeout: int) -> LegislativeTerm | None:
    result = await asyncio.wait_for(
        db_session.execute(
            select(LegislativeTerm)
            .where(
                LegislativeTerm.endDate.is_not(None),  # type: ignore[union-attr]
                LegislativeTerm.endDate < datetime.now(),  # type: ignore[operator]
                or_(LegislativeTerm.deleted.is_(False), LegislativeTerm.deleted.is_(None)),  # type: ignore[union-attr]
            )
            .order_by(LegislativeTerm.endDate.desc())  # type: ignore[union-attr]
            .limit(1)
        ),
        timeout=query_timeout,
    )
    return result.scalars().first()


@log_execution_time
async def query_faction_activity(
    db_session,
    *,
    paper_type: PaperTypeEnum | None = None,
    paper_subtype: PaperSubtypeEnum | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    period: Literal["previous_legislative_term"] | None = None,
    faction_name: str | None = None,
    ranking: Literal["descending", "ascending"] = "descending",
    limit: int | None = None,
    timeout: int = 30,
):
    """Return faction counts, including all ties at the limit boundary."""
    if ranking not in ("ascending", "descending"):
        raise ValueError("ranking must be 'ascending' or 'descending'")
    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1")

    term: LegislativeTerm | None = None

    if period == "previous_legislative_term":
        term = await _completed_legislative_term(db_session, timeout)
        if term is None or term.startDate is None or term.endDate is None:
            raise ValueError("No completed legislative term with a valid date range was found")
        start_date = term.startDate.date()
        end_date = term.endDate.date()

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    paper_conditions = [
        Paper.db_id == PaperOriginatorOrgLink.paper_id,
        or_(Paper.deleted.is_(False), Paper.deleted.is_(None)),
    ]

    if paper_type is not None:
        paper_conditions.append(Paper.paper_type == paper_type.value)

    if paper_subtype is not None:
        paper_conditions.append(Paper.paper_subtype == paper_subtype.value)

    if start_date is not None:
        paper_conditions.append(Paper.date >= datetime.combine(start_date, datetime_time.min))

    if end_date is not None:
        paper_conditions.append(Paper.date < datetime.combine(end_date + timedelta(days=1), datetime_time.min))

    counts_statement = (
        select(
            Organization.db_id.label("organization_id"),
            Organization.name.label("name"),
            Organization.shortName.label("short_name"),
            func.count(distinct(Paper.db_id)).label("paper_count"),
        )
        .select_from(Organization)
        .outerjoin(
            PaperOriginatorOrgLink,
            Organization.db_id == PaperOriginatorOrgLink.organization_id,
        )
        .outerjoin(Paper, and_(*paper_conditions))
        .where(
            or_(
                Organization.classification == OrganizationClassificationEnum.FACTION.value,
                Organization.organizationType == OrganizationTypeEnum.FACTION.value,
            ),
            or_(
                Organization.deleted.is_(False),
                Organization.deleted.is_(None),
            ),
        )
        .group_by(
            Organization.db_id,
            Organization.name,
            Organization.shortName,
        )
    )

    if faction_name and faction_name.strip():
        normalized = faction_name.strip().casefold()
        counts_statement = counts_statement.where(
            or_(
                func.lower(Organization.name) == normalized,
                func.lower(Organization.shortName) == normalized,
            )
        )

    counts = counts_statement.cte("faction_counts")
    ascending = ranking == "ascending"
    count_order = counts.c.paper_count.asc() if ascending else counts.c.paper_count.desc()

    statement = select(
        counts.c.name,
        counts.c.short_name,
        counts.c.paper_count,
    )

    if limit is not None:
        # Die ersten N Anzahlen bestimmen die Grenze.
        top_counts = select(counts.c.paper_count).select_from(counts).order_by(count_order).limit(limit).subquery("top_counts")

        cutoff = (
            select(func.max(top_counts.c.paper_count) if ascending else func.min(top_counts.c.paper_count))
            .select_from(top_counts)
            .scalar_subquery()
        )

        # Alle Fraktionen an der Grenze einschließen.
        statement = statement.where(counts.c.paper_count <= cutoff if ascending else counts.c.paper_count >= cutoff)

    statement = statement.order_by(
        count_order,
        counts.c.name.asc(),
        counts.c.short_name.asc(),
        counts.c.organization_id.asc(),
    )

    result = await asyncio.wait_for(
        db_session.execute(statement),
        timeout=timeout,
    )
    rows = result.all()
    logger.info(
        "query_faction_activity: faction_name=%r, paper_type=%r, "
        "paper_subtype=%r, start_date=%r, end_date=%r, "
        "ranking=%r, limit=%r, rows=%r",
        faction_name,
        paper_type,
        paper_subtype,
        start_date,
        end_date,
        ranking,
        limit,
        rows,
    )

    return rows, term, start_date, end_date
