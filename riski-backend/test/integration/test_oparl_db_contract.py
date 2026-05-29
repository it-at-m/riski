import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from uuid import UUID

import pytest
from app.api.dependencies import get_db_session
from app.backend import get_backend
from core.model.data_models import (
    AgendaItem,
    Body,
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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

DB_URL_ENV = "RISKI_TEST_DB_ASYNC_URL"


def _db_url() -> str:
    db_url = os.getenv(DB_URL_ENV)
    if not db_url:
        pytest.skip(f"{DB_URL_ENV} is not set; skipping DB-backed OParl contract tests", allow_module_level=True)
    return db_url


@pytest.fixture(scope="module")
def db_sessionmaker() -> Iterator[async_sessionmaker[AsyncSession]]:
    db_url = _db_url()
    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)

    async def _prepare() -> async_sessionmaker[AsyncSession]:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    sessionmaker = asyncio.run(_prepare())

    yield sessionmaker

    async def _teardown() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_teardown())


async def _seed_base_data(sessionmaker: async_sessionmaker[AsyncSession]) -> dict[str, UUID]:
    async with sessionmaker() as session:
        system = System(
            id="https://example.org/system/1",
            name="RISKI OParl",
            oparlVersion="https://schema.oparl.org/1.1/",
            contactEmail="api@example.org",
        )

        body = Body(
            id="https://example.org/body/1",
            name="Body 1",
            organization="https://example.org/body/1/organization",
            person="https://example.org/body/1/person",
            meeting="https://example.org/body/1/meeting",
            paper="https://example.org/body/1/paper",
            legislativeTerm="https://example.org/body/1/legislativeTerm",
            agendaItem="https://example.org/body/1/agendaItem",
            file="https://example.org/body/1/file",
            legislativeTermList="https://example.org/body/1/legislativeTermList",
            membership="https://example.org/body/1/membership",
            system_id=system.db_id,
        )

        organization = Organization(id="https://example.org/organization/1", name="Organization 1")
        person = Person(id="https://example.org/person/1", name="Person 1", familyName="Family", givenName="Given")

        file_obj = File(id="https://example.org/file/1", name="File 1", accessUrl="https://files.example.org/1.pdf")
        meeting = Meeting(id="https://example.org/meeting/1", name="Meeting 1", invitation=file_obj.db_id)
        location = Location(id="https://example.org/location/1", description="Location 1")

        paper = Paper(id="https://example.org/paper/1", name="Paper 1", reference="A-1", subject="Subject", mainFile_id=file_obj.db_id)
        agenda_item = AgendaItem(id="https://example.org/agendaitem/1", name="AgendaItem 1", meeting=meeting.db_id, order=1)
        membership = Membership(id="https://example.org/membership/1", organization=organization.db_id, role="member")

        legislative_term = LegislativeTerm(id="https://example.org/legislative-term/1", name="LegislativeTerm 1")

        active_body = body
        deleted_body = Body(
            id="https://example.org/body/2",
            name="Body 2",
            organization="https://example.org/body/2/organization",
            person="https://example.org/body/2/person",
            meeting="https://example.org/body/2/meeting",
            paper="https://example.org/body/2/paper",
            legislativeTerm="https://example.org/body/2/legislativeTerm",
            agendaItem="https://example.org/body/2/agendaItem",
            file="https://example.org/body/2/file",
            legislativeTermList="https://example.org/body/2/legislativeTermList",
            membership="https://example.org/body/2/membership",
            deleted=True,
            modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        active_body.modified = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Persist parents first so dependent FK rows are always valid on flush.
        session.add_all(
            [
                system,
                active_body,
                deleted_body,
                organization,
                person,
                file_obj,
                meeting,
                location,
                legislative_term,
            ]
        )
        await session.flush()

        # Dependent rows and link-table relationships are attached only after parent rows exist.
        session.add(membership)
        await session.flush()

        person.membership = [membership]
        meeting.agenda_items = [agenda_item]
        meeting.auxiliary_files = [file_obj]
        paper.auxiliary_files = [file_obj]
        paper.locations = [location]
        session.add_all([agenda_item, paper])
        await session.commit()

        return {
            "person_id": person.db_id,
            "meeting_id": meeting.db_id,
            "paper_id": paper.db_id,
        }


@pytest.fixture(scope="module")
def db_backed_client(db_sessionmaker: async_sessionmaker[AsyncSession]) -> Iterator[tuple[TestClient, dict[str, UUID]]]:
    async def _override_db_session() -> AsyncIterator[AsyncSession]:
        async with db_sessionmaker() as session:
            yield session

    ids = asyncio.run(_seed_base_data(db_sessionmaker))

    backend = get_backend()
    backend.dependency_overrides[get_db_session] = _override_db_session
    client = TestClient(backend)

    yield client, ids

    backend.dependency_overrides.clear()


def test_db_backed_filters_control_total_elements(db_backed_client: tuple[TestClient, dict[str, UUID]]) -> None:
    client, _ = db_backed_client

    default_response = client.get("/api/oparl/v1.1/body?page=1&limit=10")
    assert default_response.status_code == 200
    default_payload = default_response.json()
    assert len(default_payload["data"]) == 1
    assert default_payload["pagination"]["totalElements"] == 1

    modified_since_response = client.get("/api/oparl/v1.1/body?page=1&limit=10&modified_since=2024-01-01T00:00:00Z")
    assert modified_since_response.status_code == 200
    modified_payload = modified_since_response.json()
    assert len(modified_payload["data"]) == 2
    assert modified_payload["pagination"]["totalElements"] == 2


def test_db_backed_embedded_and_omit_internal(db_backed_client: tuple[TestClient, dict[str, UUID]]) -> None:
    client, ids = db_backed_client

    person_detail = client.get(f"/api/oparl/v1.1/person/{ids['person_id']}").json()
    assert "membership" in person_detail
    assert len(person_detail["membership"]) == 1

    meeting_detail = client.get(f"/api/oparl/v1.1/meeting/{ids['meeting_id']}").json()
    assert "agendaItem" in meeting_detail
    assert "auxiliaryFile" in meeting_detail

    paper_detail = client.get(f"/api/oparl/v1.1/paper/{ids['paper_id']}").json()
    assert "auxiliaryFile" in paper_detail
    assert "location" in paper_detail

    person_omit = client.get("/api/oparl/v1.1/person?page=1&limit=1&omit_internal=true").json()["data"][0]
    meeting_omit = client.get("/api/oparl/v1.1/meeting?page=1&limit=1&omit_internal=true").json()["data"][0]
    paper_omit = client.get("/api/oparl/v1.1/paper?page=1&limit=1&omit_internal=true").json()["data"][0]

    assert "membership" not in person_omit
    assert "agendaItem" not in meeting_omit
    assert "auxiliaryFile" not in meeting_omit
    assert "auxiliaryFile" not in paper_omit
    assert "location" not in paper_omit


def test_db_backed_error_and_cors_contract(db_backed_client: tuple[TestClient, dict[str, UUID]]) -> None:
    client, _ = db_backed_client

    not_found = client.get("/api/oparl/v1.1/body/00000000-0000-0000-0000-000000000000")
    assert not_found.status_code == 404
    error_payload = not_found.json()
    assert error_payload["type"] == "https://schema.oparl.org/1.1/Error"
    assert error_payload["status"] == 404

    list_response = client.get("/api/oparl/v1.1/body?page=1&limit=1")
    assert list_response.status_code == 200
    assert list_response.headers.get("access-control-allow-origin") == "*"
