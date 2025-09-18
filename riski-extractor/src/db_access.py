from config.config import get_config
from sqlmodel import Session, SQLModel, create_engine, select

from src.data_models import Person

_engine = create_engine(str(get_config().database_url), echo=True)
_session = Session(_engine)


def create_tables():
    SQLModel.metadata.create_all(_engine)


def request_person_by_risid(risid: str, session=None):
    """
    Load a Person Object from the DB based on the risId.
    This is used to create the correct relations in the Database.
    """
    statement = select(Person).where(Person.id == risid)

    person = (_session if not session else session).exec(statement).one()
    return person


def save_object_to_database(object):
    _session.add(object)
    _session.commit()


def save_objects_to_database(objects: list[object]):
    for object in objects:
        _session.add(object)
    _session.commit()
