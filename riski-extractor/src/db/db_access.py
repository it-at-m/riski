from sqlmodel import select
from src.data_models import Keyword, PaperType, Person
from src.db.db import get_session


def request_object_by_risid(risid: str, object_type: type, session=None):
    statement = select(object_type).where(object_type.id == risid)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def request_object_by_name(name: str, object_type: type, session=None):
    statement = select(object_type).where(object_type.name == name)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


def request_person_by_familyName(familyName: str, session=None):
    statement = select(Person).where(Person.familyName == familyName)
    sess = session or get_session()
    obj = sess.exec(statement).first()
    return obj


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


def insert_and_return_object(obj: object, session=None):
    sess = session or get_session()
    sess.add(obj)
    sess.commit()
    sess.refresh(obj)
    return obj


def get_or_insert_object_to_database(obj: object, session=None):
    sess = session or get_session()
    if isinstance(obj, Keyword) or isinstance(obj, PaperType):
        obj_db = request_object_by_name(obj.name, type(obj), sess)
    else:
        obj_db = request_object_by_risid(obj.id, type(obj), sess)
    if not obj_db:
        obj_db = insert_and_return_object(obj, sess)
    return obj_db
