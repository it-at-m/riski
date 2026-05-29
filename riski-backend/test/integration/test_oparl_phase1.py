from http import HTTPStatus
from typing import Any
from uuid import UUID

from app.api.dependencies import get_db_session
from app.backend import get_backend
from core.model.data_models import (
    AgendaItem,
    Body,
    Consultation,
    File,
    LegislativeTerm,
    Location,
    Meeting,
    Membership,
    Organization,
    Paper,
    Person,
    System,
)
from fastapi.testclient import TestClient


class _ScalarCollection:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return list(self._items)

    def first(self) -> Any | None:
        return self._items[0] if self._items else None


class _FakeExecuteResult:
    def __init__(self, *, items: list[Any] | None = None, count: int | None = None):
        self._items = items or []
        self._count = count

    def scalars(self) -> _ScalarCollection:
        return _ScalarCollection(self._items)

    def scalar_one(self) -> int:
        if self._count is None:
            raise AssertionError("count was requested from a non-count result")
        return self._count


class _FakeSession:
    def __init__(
        self,
        *,
        system: System,
        bodies: list[Body],
        organizations: list[Organization],
        persons: list[Person],
        memberships: list[Membership],
        legislative_terms: list[LegislativeTerm],
        meetings: list[Meeting],
        agenda_items: list[AgendaItem],
        papers: list[Paper],
        files: list[File],
        consultations: list[Consultation],
        locations: list[Location],
    ):
        self._system = system
        self._bodies = bodies
        self._organizations = organizations
        self._persons = persons
        self._memberships = memberships
        self._legislative_terms = legislative_terms
        self._meetings = meetings
        self._agenda_items = agenda_items
        self._papers = papers
        self._files = files
        self._consultations = consultations
        self._locations = locations

    def _get_collection(self, table_name: str) -> list[Any]:
        collections: dict[str, list[Any]] = {
            "body": self._bodies,
            "organization": self._organizations,
            "person": self._persons,
            "membership": self._memberships,
            "legislative_term": self._legislative_terms,
            "meeting": self._meetings,
            "agenda_item": self._agenda_items,
            "paper": self._papers,
            "file": self._files,
            "consultation": self._consultations,
            "location": self._locations,
        }
        try:
            return collections[table_name]
        except KeyError as exc:
            raise AssertionError(f"Unsupported table in fake session: {table_name}") from exc

    def _extract_table_name(self, sql: str) -> str:
        for table_name in [
            "legislative_term",
            "organization",
            "membership",
            "agenda_item",
            "consultation",
            "meeting",
            "location",
            "person",
            "paper",
            "file",
            "body",
        ]:
            if f"from {table_name}" in sql:
                return table_name
        raise AssertionError(f"Unexpected statement for fake session: {sql}")

    async def execute(self, statement: Any) -> _FakeExecuteResult:
        sql = str(statement).lower()
        if "from system" in sql:
            return _FakeExecuteResult(items=[self._system])

        table_name = self._extract_table_name(sql)
        collection = self._get_collection(table_name)

        if "count(" in sql:
            if "deleted is null" in sql or "deleted is false" in sql:
                collection = [entry for entry in collection if getattr(entry, "deleted", None) in (None, False)]
            return _FakeExecuteResult(count=len(collection))

        if "where" in sql:
            compiled = statement.compile()
            if "db_id_1" in compiled.params:
                raw_id = compiled.params.get("db_id_1")
                requested_id = UUID(str(raw_id)) if raw_id is not None else None
                item = next((entry for entry in collection if entry.db_id == requested_id), None)
                return _FakeExecuteResult(items=[item] if item else [])

        # Simulate default soft-delete behavior for list endpoints if query includes deleted filter.
        if "deleted is null" in sql or "deleted is false" in sql:
            collection = [entry for entry in collection if getattr(entry, "deleted", None) in (None, False)]

        return _FakeExecuteResult(items=collection)


def _build_system() -> System:
    return System(
        id="https://ris.example.org/system",
        name="RISKI OParl",
        oparlVersion="https://schema.oparl.org/1.1/",
        contactEmail="api@example.org",
    )


def _build_body(seed: int) -> Body:
    return Body(
        id=f"https://ris.example.org/body/{seed}",
        name=f"Body {seed}",
        organization=f"https://ris.example.org/body/{seed}/organization",
        person=f"https://ris.example.org/body/{seed}/person",
        meeting=f"https://ris.example.org/body/{seed}/meeting",
        paper=f"https://ris.example.org/body/{seed}/paper",
        legislativeTerm=f"https://ris.example.org/body/{seed}/legislativeTerm",
        agendaItem=f"https://ris.example.org/body/{seed}/agendaItem",
        file=f"https://ris.example.org/body/{seed}/file",
        legislativeTermList=f"https://ris.example.org/body/{seed}/legislativeTermList",
        membership=f"https://ris.example.org/body/{seed}/membership",
    )


def _build_organization(seed: int) -> Organization:
    return Organization(
        id=f"https://ris.example.org/organization/{seed}",
        name=f"Organization {seed}",
    )


def _build_person(seed: int) -> Person:
    return Person(
        id=f"https://ris.example.org/person/{seed}",
        name=f"Person {seed}",
        familyName=f"Family{seed}",
        givenName=f"Given{seed}",
    )


def _build_membership(seed: int, organization_id: UUID) -> Membership:
    return Membership(
        id=f"https://ris.example.org/membership/{seed}",
        organization=organization_id,
        role="member",
    )


def _build_legislative_term(seed: int) -> LegislativeTerm:
    return LegislativeTerm(
        id=f"https://ris.example.org/legislative-term/{seed}",
        name=f"Legislative term {seed}",
    )


def _build_file(seed: int) -> File:
    return File(
        id=f"https://ris.example.org/file/{seed}",
        name=f"File {seed}",
        accessUrl=f"https://files.example.org/{seed}.pdf",
    )


def _build_meeting(seed: int, file_id: UUID) -> Meeting:
    return Meeting(
        id=f"https://ris.example.org/meeting/{seed}",
        name=f"Meeting {seed}",
        invitation=file_id,
        resultsProtocol=file_id,
        verbatimProtocol=file_id,
    )


def _build_agenda_item(seed: int, meeting_id: UUID, file_id: UUID) -> AgendaItem:
    return AgendaItem(
        id=f"https://ris.example.org/agendaitem/{seed}",
        name=f"AgendaItem {seed}",
        meeting=meeting_id,
        order=seed,
        resolutionFile=file_id,
    )


def _build_paper(seed: int, file_id: UUID) -> Paper:
    return Paper(
        id=f"https://ris.example.org/paper/{seed}",
        name=f"Paper {seed}",
        mainFile_id=file_id,
    )


def _build_consultation(seed: int, paper_id: UUID, agenda_item_id: UUID, meeting_id: UUID) -> Consultation:
    return Consultation(
        id=f"https://ris.example.org/consultation/{seed}",
        paper=paper_id,
        agenda_item=agenda_item_id,
        meeting=meeting_id,
    )


def _build_location(seed: int) -> Location:
    return Location(
        id=f"https://ris.example.org/location/{seed}",
        description=f"Location {seed}",
    )


def test_oparl_system_returns_entrypoint() -> None:
    backend = get_backend()
    org = _build_organization(1)
    file_one = _build_file(1)
    meeting_one = _build_meeting(1, file_one.db_id)
    agenda_item_one = _build_agenda_item(1, meeting_one.db_id, file_one.db_id)
    paper_one = _build_paper(1, file_one.db_id)
    consultation_one = _build_consultation(1, paper_one.db_id, agenda_item_one.db_id, meeting_one.db_id)
    location_one = _build_location(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[_build_body(1)],
        organizations=[org],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, org.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[meeting_one],
        agenda_items=[agenda_item_one],
        papers=[paper_one],
        files=[file_one],
        consultations=[consultation_one],
        locations=[location_one],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get("/api/oparl/v1.1/system")

    backend.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "https://schema.oparl.org/1.1/System"
    assert payload["id"].endswith("/api/oparl/v1.1/system")
    assert payload["body"].endswith("/api/oparl/v1.1/body")


def test_oparl_body_list_and_detail() -> None:
    backend = get_backend()
    body_one = _build_body(1)
    body_two = _build_body(2)
    org = _build_organization(1)
    file_one = _build_file(1)
    meeting_one = _build_meeting(1, file_one.db_id)
    agenda_item_one = _build_agenda_item(1, meeting_one.db_id, file_one.db_id)
    paper_one = _build_paper(1, file_one.db_id)
    consultation_one = _build_consultation(1, paper_one.db_id, agenda_item_one.db_id, meeting_one.db_id)
    location_one = _build_location(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[body_one, body_two],
        organizations=[org],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, org.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[meeting_one],
        agenda_items=[agenda_item_one],
        papers=[paper_one],
        files=[file_one],
        consultations=[consultation_one],
        locations=[location_one],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    list_response = client.get("/api/oparl/v1.1/body?page=1&limit=1")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert "data" in list_payload
    assert "pagination" in list_payload
    assert "links" in list_payload
    assert list_payload["pagination"]["elementsPerPage"] == 1

    detail_response = client.get(f"/api/oparl/v1.1/body/{body_one.db_id}")

    backend.dependency_overrides.clear()
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"].endswith(f"/api/oparl/v1.1/body/{body_one.db_id}")
    assert detail_payload["organization"].endswith("/api/oparl/v1.1/organization")
    assert detail_payload["consultation"].endswith("/api/oparl/v1.1/consultation")


def test_oparl_phase2a_entity_endpoints() -> None:
    backend = get_backend()
    body_one = _build_body(1)
    organization_one = _build_organization(1)
    person_one = _build_person(1)
    membership_one = _build_membership(1, organization_one.db_id)
    legislative_term_one = _build_legislative_term(1)

    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[body_one],
        organizations=[organization_one],
        persons=[person_one],
        memberships=[membership_one],
        legislative_terms=[legislative_term_one],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    list_paths = ["organization", "person", "membership", "legislativeTerm"]
    detail_paths = {
        "organization": organization_one.db_id,
        "person": person_one.db_id,
        "membership": membership_one.db_id,
        "legislativeTerm": legislative_term_one.db_id,
    }

    for path in list_paths:
        list_response = client.get(f"/api/oparl/v1.1/{path}?page=1&limit=1")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert "data" in payload
        assert "pagination" in payload
        assert "links" in payload

    for path, db_id in detail_paths.items():
        detail_response = client.get(f"/api/oparl/v1.1/{path}/{db_id}")
        assert detail_response.status_code == 200
        payload = detail_response.json()
        assert payload["id"].endswith(f"/api/oparl/v1.1/{path}/{db_id}")

    backend.dependency_overrides.clear()


def test_oparl_phase2b_entity_endpoints() -> None:
    backend = get_backend()
    body_one = _build_body(1)
    organization_one = _build_organization(1)
    person_one = _build_person(1)
    membership_one = _build_membership(1, organization_one.db_id)
    legislative_term_one = _build_legislative_term(1)
    file_one = _build_file(1)
    meeting_one = _build_meeting(1, file_one.db_id)
    agenda_item_one = _build_agenda_item(1, meeting_one.db_id, file_one.db_id)
    paper_one = _build_paper(1, file_one.db_id)
    consultation_one = _build_consultation(1, paper_one.db_id, agenda_item_one.db_id, meeting_one.db_id)
    location_one = _build_location(1)

    # Wire internal/embedded relationships used in serializers.
    person_one.membership = [membership_one]
    meeting_one.agenda_items = [agenda_item_one]
    meeting_one.auxiliary_files = [file_one]
    paper_one.auxiliary_files = [file_one]
    paper_one.locations = [location_one]

    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[body_one],
        organizations=[organization_one],
        persons=[person_one],
        memberships=[membership_one],
        legislative_terms=[legislative_term_one],
        meetings=[meeting_one],
        agenda_items=[agenda_item_one],
        papers=[paper_one],
        files=[file_one],
        consultations=[consultation_one],
        locations=[location_one],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    list_paths = ["meeting", "agendaItem", "paper", "file", "consultation", "location"]
    detail_paths = {
        "meeting": meeting_one.db_id,
        "agendaItem": agenda_item_one.db_id,
        "paper": paper_one.db_id,
        "file": file_one.db_id,
        "consultation": consultation_one.db_id,
        "location": location_one.db_id,
    }

    for path in list_paths:
        list_response = client.get(f"/api/oparl/v1.1/{path}?page=1&limit=1")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert "data" in payload
        assert "pagination" in payload
        assert "links" in payload

    for path, db_id in detail_paths.items():
        detail_response = client.get(f"/api/oparl/v1.1/{path}/{db_id}")
        assert detail_response.status_code == 200
        payload = detail_response.json()
        assert payload["id"].endswith(f"/api/oparl/v1.1/{path}/{db_id}")

    person_detail = client.get(f"/api/oparl/v1.1/person/{person_one.db_id}").json()
    assert "membership" in person_detail
    assert len(person_detail["membership"]) == 1

    meeting_detail = client.get(f"/api/oparl/v1.1/meeting/{meeting_one.db_id}").json()
    assert "agendaItem" in meeting_detail
    assert "auxiliaryFile" in meeting_detail
    assert len(meeting_detail["agendaItem"]) == 1
    assert len(meeting_detail["auxiliaryFile"]) == 1

    paper_detail = client.get(f"/api/oparl/v1.1/paper/{paper_one.db_id}").json()
    assert "auxiliaryFile" in paper_detail
    assert "location" in paper_detail
    assert len(paper_detail["auxiliaryFile"]) == 1
    assert len(paper_detail["location"]) == 1

    person_omit = client.get("/api/oparl/v1.1/person?page=1&limit=1&omit_internal=true").json()["data"][0]
    meeting_omit = client.get("/api/oparl/v1.1/meeting?page=1&limit=1&omit_internal=true").json()["data"][0]
    paper_omit = client.get("/api/oparl/v1.1/paper?page=1&limit=1&omit_internal=true").json()["data"][0]

    assert "membership" not in person_omit
    assert "agendaItem" not in meeting_omit
    assert "auxiliaryFile" not in meeting_omit
    assert "auxiliaryFile" not in paper_omit
    assert "location" not in paper_omit

    backend.dependency_overrides.clear()


def test_oparl_list_filters_deleted_and_modified_since_behavior() -> None:
    backend = get_backend()

    active_body = _build_body(1)
    deleted_body = _build_body(2)
    deleted_body.deleted = True

    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[active_body, deleted_body],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    default_response = client.get("/api/oparl/v1.1/body?page=1&limit=10")
    assert default_response.status_code == 200
    default_payload = default_response.json()
    assert len(default_payload["data"]) == 1
    assert default_payload["pagination"]["totalElements"] == 1
    assert default_payload["pagination"]["totalPages"] == 1

    modified_since_response = client.get("/api/oparl/v1.1/body?page=1&limit=10&modified_since=2024-01-01T00:00:00Z")
    assert modified_since_response.status_code == 200
    modified_since_payload = modified_since_response.json()
    assert len(modified_since_payload["data"]) == 2
    assert modified_since_payload["pagination"]["totalElements"] == 2
    assert modified_since_payload["pagination"]["totalPages"] == 1

    backend.dependency_overrides.clear()


def test_oparl_links_preserve_filter_query_params() -> None:
    backend = get_backend()

    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[_build_body(1)],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get(
        "/api/oparl/v1.1/organization?"
        "page=1&limit=10&created_since=2024-01-01T00:00:00Z&"
        "created_until=2025-01-01T00:00:00Z&omit_internal=true"
    )
    assert response.status_code == 200
    links = response.json()["links"]
    assert "created_since=2024-01-01T00%3A00%3A00Z" in links["self"]
    assert "created_until=2025-01-01T00%3A00%3A00Z" in links["self"]
    assert "omit_internal=true" in links["self"]
    assert links["web"] == links["self"]

    backend.dependency_overrides.clear()


def test_omit_internal_removes_body_legislative_term() -> None:
    backend = get_backend()

    body_with_internal = _build_body(1)
    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[body_with_internal],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get("/api/oparl/v1.1/body?page=1&limit=10&omit_internal=true")
    assert response.status_code == 200

    payload = response.json()
    assert payload["data"]
    body_payload = payload["data"][0]
    assert "legislativeTerm" not in body_payload

    backend.dependency_overrides.clear()


def test_oparl_not_found_returns_oparl_error_object() -> None:
    backend = get_backend()
    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[_build_body(1)],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get("/api/oparl/v1.1/body/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    payload = response.json()
    assert payload["type"] == "https://schema.oparl.org/1.1/Error"
    assert payload["title"] == "Not Found"
    assert payload["status"] == 404
    assert payload["message"] == "Body not found"

    backend.dependency_overrides.clear()


def test_oparl_validation_returns_oparl_error_object() -> None:
    backend = get_backend()
    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[_build_body(1)],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get("/api/oparl/v1.1/body?page=0&limit=10")
    assert response.status_code == 422
    payload = response.json()
    assert payload["type"] == "https://schema.oparl.org/1.1/Error"
    assert payload["title"] == HTTPStatus(422).phrase
    assert payload["status"] == 422
    assert payload["message"] == "Request validation failed"
    assert payload["details"]

    backend.dependency_overrides.clear()


def test_oparl_list_response_includes_cors_headers() -> None:
    backend = get_backend()
    organization_one = _build_organization(1)
    fake_session = _FakeSession(
        system=_build_system(),
        bodies=[_build_body(1)],
        organizations=[organization_one],
        persons=[_build_person(1)],
        memberships=[_build_membership(1, organization_one.db_id)],
        legislative_terms=[_build_legislative_term(1)],
        meetings=[],
        agenda_items=[],
        papers=[],
        files=[],
        consultations=[],
        locations=[],
    )

    async def _override_db_session():
        yield fake_session

    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    response = client.get("/api/oparl/v1.1/body?page=1&limit=1")
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
    assert "GET" in (response.headers.get("access-control-allow-methods") or "")

    backend.dependency_overrides.clear()
