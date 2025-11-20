from sqlmodel import select
from src.data_models import Keyword, Paper, Person
from src.db.db import get_session
from src.filehandler.file_id_collector import collect_file_id


def request_object_by_risid(risid: str, object_type: type, session=None):
    statement = select(object_type).where(object_type.id == risid)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def request_all(object_type: type, session=None) -> list[object]:
    statement = select(object_type)
    sess = session or get_session()
    objects = sess.exec(statement).all()
    return objects


def request_object_by_name(name: str, object_type: type, session=None):
    statement = select(object_type).where(object_type.name == name)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def insert_and_return_object(obj: object, session=None):
    sess = session or get_session()
    try:
        sess.add(obj)
        sess.commit()
        sess.refresh(obj)
        return obj
    except Exception:
        sess.rollback()
        raise


def request_person_by_familyName(familyName: str, logger, session=None):
    statement = select(Person).where(Person.familyName == familyName)
    sess = session or get_session()
    results = sess.exec(statement).all()
    if len(results) > 1:
        logger.warning(f"Multiple Person records found for familyName '{familyName}'. Returning first match.")
    return results[0] if results else None


def update_or_insert_objects_to_database(objects: list[object], session=None):
    sess = session or get_session()
    for obj in objects:
        obj_db = request_object_by_risid(obj.id, type(obj), sess)
        if obj_db:
            update_object(obj, obj_db, sess)
        else:
            insert_object_to_database(obj, sess)


def update_object(obj: object, obj_db: object, session=None):
    sess = session or get_session()

    for field, value in obj.__dict__.items():
        if field not in ("db_id", "created", "modified") and not field.startswith("_"):
            setattr(obj_db, field, value)

    sess.add(obj_db)
    sess.commit()


def insert_object_to_database(obj: object, session=None):
    sess = session or get_session()
    sess.add(obj)
    sess.commit()


@collect_file_id
def get_or_insert_object_to_database(obj: object, session=None):
    """
    Retrieves or inserts an object into the database.

    Args:
        obj (object): The object to retrieve or insert, identified by 'name' (for Keyword/PaperType)
                      or 'id' (for others).
        session (Session, optional): Optional SQLAlchemy session.

    Returns:
        object: The retrieved or inserted object.
    """
    sess = session or get_session()
    if isinstance(obj, Keyword):
        obj_db = request_object_by_name(obj.name, type(obj), sess)
    else:
        obj_db = request_object_by_risid(obj.id, type(obj), sess)
    if not obj_db:
        obj_db = insert_and_return_object(obj, sess)
    return obj_db


def request_paper_by_reference(reference: str, logger, session=None) -> None | Paper:
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


def request_person_by_full_name(familyName: str, givenName: str, logger, session=None) -> Person | None:
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
