from config import get_config
from sqlmodel import Session, SQLModel, create_engine, select

from src.data_models import Person

_engine = create_engine(str(get_config().database_url), echo=True)


def create_tables():
    SQLModel.metadata.create_all(_engine)


def request_person_by_risid(risid: str):
    with Session(_engine) as session:
        statement = select(Person).where(Person.id == risid)
        return session.exec(statement).first()


def save_object_to_database(object):
    with Session(_engine) as session:
        session.add(object)
        session.commit()


def save_objects_to_database(objects: list[object]):
    for object in objects:
        save_object_to_database(object)
