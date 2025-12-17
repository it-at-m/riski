import time
from contextlib import contextmanager
from functools import wraps
from typing import List, TypeVar, overload

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Session, select
from src.logtools import getLogger

from core.db.db import get_session
from core.model.data_models import RIS_NAME_OBJECT, RIS_PARSED_DB_OBJECT, Keyword, Paper, Person

T = TypeVar("T", bound=RIS_PARSED_DB_OBJECT)
N = TypeVar("N", bound=RIS_NAME_OBJECT)

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
    """Yield a session from `get_session()`.

    Use as: `with _get_session_ctx() as sess:`
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()


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


@log_execution_time
@overload
def request_object_by_name(name: str, object_type: type[N], session: Session | None = None) -> N | None: ...


@log_execution_time
@overload
def request_object_by_name(name: str, object_type: type[Keyword], session: Session | None = None) -> Keyword | None: ...


@log_execution_time
def request_object_by_name(name: str, object_type: type[N] | type[Keyword], session: Session | None = None) -> N | Keyword | None:
    if session:
        statement = select(object_type).where(object_type.name == name)
        obj = session.exec(statement).first()
        return obj
    else:
        with _get_session_ctx() as sess:
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
def insert_and_return_object(obj: RIS_PARSED_DB_OBJECT | Keyword) -> RIS_PARSED_DB_OBJECT | Keyword:
    with _get_session_ctx() as session:
        try:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        except Exception:
            session.rollback()
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
        with _get_session_ctx() as sess:
            obj_db = request_object_by_risid(obj.id, type(obj), sess)
            if obj_db:
                logger.debug("updating existing %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                update_object(obj, obj_db, sess)
            else:
                logger.debug("inserting new %s id=%s (item %d/%d)", type(obj).__name__, getattr(obj, "id", None), idx, total)
                insert_object_to_database(obj, sess)


@log_execution_time
def update_object(obj: T, obj_db: T, session: Session) -> None:
    mapper = inspect(obj.__class__)
    for field, value in obj.__dict__.items():
        if field not in ("db_id", "created", "modified") and not field.startswith("_"):
            # Check if the attribute is a relationship field
            prop = mapper.all_orm_descriptors.get(field)
            if prop and isinstance(prop.property, RelationshipProperty):
                # One-to-many or many-to-many relationship
                if prop.property.uselist:
                    for related_obj in value:
                        session.merge(related_obj)
                # Many-to-one or one-to-one relationship
                else:
                    if value is not None:
                        session.merge(value)
            else:
                setattr(obj_db, field, value)

    session.add(obj_db)
    session.commit()


@log_execution_time
def insert_object_to_database(obj: T, session: Session) -> None:
    session.add(obj)
    session.commit()


@log_execution_time
def get_or_insert_object_to_database(obj: RIS_PARSED_DB_OBJECT | Keyword) -> RIS_PARSED_DB_OBJECT | Keyword:
    """
    Retrieves or inserts an object into the database.

    Args:
        obj (T | Keyword): The object to retrieve or insert, identified by 'name' (keyword)
                 or 'id' (for others).
        session (Session | None): Optional SQLAlchemy session.

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
        obj_db = insert_and_return_object(obj)
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
