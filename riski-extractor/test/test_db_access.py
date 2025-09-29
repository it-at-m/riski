from src.data_models import Person
from src.db.db_access import request_object_by_risid


# ----------------------
# Test Person
# ----------------------
def test_request_person_by_risid(session, person):
    db_person = request_object_by_risid(risid=person.id, t=Person, session=session)
    assert db_person.db_id == person.db_id
    assert db_person.id == person.id
    assert db_person.name == person.name
    assert db_person.title == person.title
    assert db_person.created == person.created
    assert db_person.modified == person.modified
