from datetime import datetime, timezone

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
    person_db.affix = person.affix
    person_db.name = person.name
    person_db.body = person.body
    person_db.deleted = person.deleted
    person_db.email = person.email
    person_db.familyName = person.familyName
    person_db.formOfAddress = person.formOfAddress
    person_db.gender = person.gender
    person_db.givenName = person.givenName
    person_db.keywords = person.keywords
    person_db.license = person.license
    person_db.life = person.life
    person_db.lifeSource = person.lifeSource
    person_db.location = person.location
    person_db.meetings = person.meetings
    person_db.membership = person.membership
    person_db.papers = person.papers
    person_db.phone = person.phone
    person_db.status = person.status
    person_db.title = person.title
    person_db.type = person.type
    person_db.web = person.web
    person_db.modified = datetime.now(timezone.utc)

    sess.commit()


def insert_person_to_database(object, session=None):
    sess = session or get_session()
    sess.add(object)
    sess.commit()
