from logging import Logger
from typing import List, TypeVar, overload

from sqlmodel import Session, select
from src.data_models import RIS_NAME_OBJECT, RIS_PARSED_DB_OBJECT, Keyword, Paper, Person
from src.db.db import get_session
from src.filehandler.file_id_collector import collect_file_id
from src.logtools import getLogger

T = TypeVar("T", bound=RIS_PARSED_DB_OBJECT)
N = TypeVar("N", bound=RIS_NAME_OBJECT)

logger: Logger = getLogger()


def request_object_by_risid(risid: str, object_type: type[T], session: Session | None = None) -> T | None:
    statement = select(object_type).where(object_type.id == risid)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def request_all(object_type: type[T], session: Session | None = None) -> List[T]:
    statement = select(object_type)
    sess = session or get_session()
    objects = sess.exec(statement).all()
    return objects


@overload
def request_object_by_name(name: str, object_type: type[N], session: Session | None = None) -> N | None: ...


@overload
def request_object_by_name(name: str, object_type: type[Keyword], session: Session | None = None) -> Keyword | None: ...


def request_object_by_name(name: str, object_type: type[N] | type[Keyword], session: Session | None = None) -> N | Keyword | None:
    statement = select(object_type).where(object_type.name == name)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def remove_object_by_id(id: str, object_type: type[T], session=None):
    statement = select(object_type).where(object_type.id == id)
    sess = session or get_session()
    obj = sess.exec(statement).one()
    sess.delete(obj)
    sess.commit()


def insert_and_return_object(obj: T, session: Session | None = None) -> T:
    sess = session or get_session()
    try:
        sess.add(obj)
        sess.commit()
        sess.refresh(obj)
        return obj
    except Exception:
        sess.rollback()
        raise


def request_person_by_familyName(familyName: str, logger: Logger, session: Session | None = None) -> Person | None:
    statement = select(Person).where(Person.familyName == familyName)
    sess = session or get_session()
    results = sess.exec(statement).all()
    if len(results) > 1:
        logger.warning(f"Multiple Person records found for familyName '{familyName}'. Returning first match.")
    return results[0] if results else None


def update_or_insert_objects_to_database(objects: List[T], session: Session | None = None) -> None:
    sess = session or get_session()
    for obj in objects:
        obj_db = request_object_by_risid(obj.id, type(obj), sess)
        if obj_db:
            update_object(obj, obj_db, sess)
        else:
            insert_object_to_database(obj, sess)


def update_object(obj: T, obj_db: T, session: Session | None = None) -> None:
    sess = session or get_session()

    for field, value in obj.__dict__.items():
        if field not in ("db_id", "created", "modified") and not field.startswith("_"):
            setattr(obj_db, field, value)

    sess.add(obj_db)
    sess.commit()


def insert_object_to_database(obj: T, session: Session | None = None) -> None:
    sess = session or get_session()
    sess.add(obj)
    sess.commit()


@collect_file_id
def get_or_insert_object_to_database(obj: T | Keyword, session: Session | None = None) -> T | Keyword:
    """
    Retrieves or inserts an object into the database.

    Args:
        obj (T | Keyword): The object to retrieve or insert, identified by 'name' (keyword)
                 or 'id' (for others).
        session (Session | None): Optional SQLAlchemy session.

    Returns:
        obj_db: The retrieved or inserted object.
    """
    sess = session or get_session()
    if isinstance(obj, Keyword):
        obj_db = request_object_by_name(obj.name, type(obj), sess)
    else:
        obj_db = request_object_by_risid(obj.id, type(obj), sess)
    if not obj_db:
        obj_db = insert_and_return_object(obj, sess)
    return obj_db


def request_paper_by_reference(reference: str, logger: Logger, session: Session | None = None) -> None | Paper:
    session = session or get_session()
    stmt = select(Paper).where(Paper.reference == reference)
    results = session.exec(stmt).all()

    if not results:
        logger.warning(f"No paper found for {reference}")
        return None
    elif len(results) > 1:
        logger.warning(f"Multiple papers found for reference '{reference}' — using the first one")

    paper = results[0]
    logger.debug(f"Found paper {reference} in DB (id={paper.id})")
    return paper


def request_person_by_full_name(
    familyName: str,
    givenName: str,
    logger: Logger,
    session: Session | None = None,
) -> Person | None:
    session = session or get_session()
    stmt = select(Person).where(Person.familyName == familyName, Person.givenName == givenName)
    results = session.exec(stmt).all()

    if not results:
        logger.warning(f"No person found for {givenName} {familyName}")
        return None
    elif len(results) > 1:
        logger.warning(f"Multiple persons found for {givenName} {familyName} — using the first one")

    person = results[0]
    logger.debug(f"Found person {givenName} {familyName} in DB (id={person.id})")
    return person


def request_batch(model: type[T], offset: int, limit: int) -> List[T]:
    """
    Loads a batch of records for a given model with offset and limit.
    """
    sess = get_session()
    statement = select(model).order_by(model.db_id).offset(offset).limit(limit)
    return sess.exec(statement).all()
