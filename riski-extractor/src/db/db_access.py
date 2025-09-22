from src.data_models import Person
from src.db.db_access_person import update_or_insert_person


def update_or_insert_objects_to_database(objects: list[object]):
    for object in objects:
        if type(object) is Person:
            update_or_insert_person(object)
