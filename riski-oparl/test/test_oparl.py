"""Unit tests for the OParl serialization layer (no database required)."""

from datetime import datetime

from core.model.data_models import Body, Meeting, Paper, Person
from core.model.data_models import File as RisFile

from app.oparl.pagination import make_list_envelope
from app.oparl.serializers import OParlSerializer
from app.oparl.urls import object_url

BASE = "https://example.org/oparl/v1"


def make_serializer() -> OParlSerializer:
    return OParlSerializer(BASE)


def test_object_url():
    paper = Paper(id="https://risi.muenchen.de/p/1", name="x")
    assert object_url(BASE, Paper, paper.db_id) == f"{BASE}/papers/{paper.db_id}"


def test_serialize_paper_basics():
    paper = Paper(
        id="https://risi.muenchen.de/risi/antrag/detail/123",
        name="Testantrag",
        reference="20-26 / A 1",
        date=datetime(2025, 1, 10, 14, 30),
    )
    out = make_serializer().serialize_paper(paper)

    assert out["id"] == f"{BASE}/papers/{paper.db_id}"
    assert out["type"] == "https://schema.oparl.org/1.1/Paper"
    assert out["web"] == "https://risi.muenchen.de/risi/antrag/detail/123"
    assert out["name"] == "Testantrag"
    assert out["reference"] == "20-26 / A 1"
    # date must be rendered as a plain date, not a datetime
    assert out["date"] == "2025-01-10"
    # empty relations / None fields are omitted
    assert "mainFile" not in out
    assert None not in out.values()


def test_web_omitted_for_non_http_id():
    # Persons synthesised from originators use urn: ids, which are not URLs.
    person = Person(id="urn:riski:person:max:mustermann", givenName="Max", familyName="Mustermann", name="Max Mustermann")
    out = make_serializer().serialize_person(person)
    assert out["id"] == f"{BASE}/people/{person.db_id}"
    assert "web" not in out
    assert out["familyName"] == "Mustermann"


def test_serialize_file_keeps_access_url():
    f = RisFile(id="https://risi.muenchen.de/f/1", name="Doc", accessUrl="https://risi.muenchen.de/files/doc.pdf")
    out = make_serializer().serialize_file(f)
    assert out["accessUrl"] == "https://risi.muenchen.de/files/doc.pdf"
    assert out["type"] == "https://schema.oparl.org/1.1/File"


def test_serialize_meeting_state_mapping():
    m = Meeting(id="https://risi.muenchen.de/m/1", name="Sitzung", meetingState="durchgeführt")
    out = make_serializer().serialize_meeting(m)
    assert out["meetingState"] == "conducted"


def test_body_has_required_lists():
    body = Body(
        id="https://risi.muenchen.de/b/1",
        name="München",
        organization="o",
        person="p",
        meeting="m",
        paper="pp",
        legislativeTerm="l",
        agendaItem="a",
        file="f",
        legislativeTermList="ll",
        membership="mm",
    )
    out = make_serializer().serialize_body(body, legislative_terms=[])
    for key in ("organization", "person", "meeting", "paper"):
        assert out[key].startswith(f"{BASE}/bodies/{body.db_id}/")
    assert out["system"] == f"{BASE}/system"
    assert out["legislativeTerm"] == []


def test_pagination_envelope_links():
    env = make_list_envelope(data=[1, 2, 3], total=120, page=2, page_size=50, list_url=f"{BASE}/bodies/x/papers")
    assert env["pagination"] == {"totalElements": 120, "elementsPerPage": 50, "currentPage": 2, "totalPages": 3}
    assert env["links"]["first"] == f"{BASE}/bodies/x/papers?page=1"
    assert env["links"]["last"] == f"{BASE}/bodies/x/papers?page=3"
    assert env["links"]["prev"] == f"{BASE}/bodies/x/papers?page=1"
    assert env["links"]["next"] == f"{BASE}/bodies/x/papers?page=3"


def test_pagination_first_page_has_no_prev():
    env = make_list_envelope(data=[], total=0, page=1, page_size=50, list_url=f"{BASE}/bodies")
    assert "prev" not in env["links"]
    assert "next" not in env["links"]
    assert env["pagination"]["totalPages"] == 1
