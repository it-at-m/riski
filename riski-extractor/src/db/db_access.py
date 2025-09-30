from sqlmodel import select
from src.db.db import get_session


def request_object_by_risid(risid: str, object_type: type, session=None):
    statement = select(object_type).where(object_type.id == risid)
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
