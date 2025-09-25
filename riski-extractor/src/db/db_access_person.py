from sqlmodel import select
from src.data_models import Person
from src.db.db import get_session


def request_person_by_risid(risid: str, session=None):
    """
    Load a Person Object from the DB based on the risId.
    This is used to create the correct relations in the Database.
    """
    statement = select(Person).where(Person.id == risid)
    sess = session or get_session()
    person = sess.exec(statement).first()
    return person


def update_or_insert_person(person: Person, session=None):
    person_db = request_person_by_risid(person.id)
    if person_db:
        update_person(person, person_db, session)
    else:
        person.modified = person.created
        insert_person_to_database(person, session)


def update_person(person: Person, person_db: Person, session=None):
    sess = session or get_session()

    for field, value in person.__dict__.items():
        if field not in ("db_id", "created", "modified") and not field.startswith("_"):
            setattr(person_db, field, value)

    sess.add(person_db)
    sess.commit()


def insert_person_to_database(object, session=None):
    sess = session or get_session()
    sess.add(object)
    sess.commit()
