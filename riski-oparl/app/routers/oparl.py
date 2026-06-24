"""OParl 1.1 REST endpoints."""

import uuid
from datetime import datetime
from typing import Annotated, Any, Callable

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
)  # noqa: F401  (all referenced as ORM models / list targets)
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.db import get_session
from app.oparl import examples as ex
from app.oparl.pagination import make_list_envelope
from app.oparl.repository import TimeFilters, get_by_id, list_objects
from app.oparl.serializers import OParlSerializer
from app.oparl.urls import body_list_url, body_sublist_url, system_url
from app.settings import OParlSettings, get_settings

router = APIRouter(prefix="/oparl/v1")

# Tag groups used to organise the Swagger UI.
TAG_SYSTEM = "OParl: System"
TAG_BODY = "OParl: Body"
TAG_LISTS = "OParl: Lists"
TAG_OBJECTS = "OParl: Objects"


# --- dependencies ----------------------------------------------------------
def _default_body_db_id(session: Session) -> uuid.UUID | None:
    body = session.exec(select(Body)).first()
    return body.db_id if body else None


def get_serializer(session: Session = Depends(get_session)) -> OParlSerializer:
    settings = get_settings()
    return OParlSerializer(settings.base_url, _default_body_db_id(session))


SettingsDep = Annotated[OParlSettings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]
SerializerDep = Annotated[OParlSerializer, Depends(get_serializer)]


def _time_filters(
    created_since: datetime | None = Query(
        None, description="Only objects created at/after this ISO-8601 timestamp.", examples=["2026-01-01T00:00:00"]
    ),
    created_until: datetime | None = Query(None, description="Only objects created at/before this ISO-8601 timestamp."),
    modified_since: datetime | None = Query(
        None,
        description="Only objects modified at/after this ISO-8601 timestamp (incremental harvesting).",
        examples=["2026-06-01T00:00:00"],
    ),
    modified_until: datetime | None = Query(None, description="Only objects modified at/before this ISO-8601 timestamp."),
) -> TimeFilters:
    return TimeFilters(
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )


FiltersDep = Annotated[TimeFilters, Depends(_time_filters)]


def _ok(example: Any) -> dict:
    """OpenAPI ``responses`` entry attaching a 200 example."""
    return {200: {"content": {"application/json": {"example": example}}}}


def _ok_obj(example: Any) -> dict:
    """200 example plus the OParl 404 error example, for object-by-id endpoints."""
    return {
        **_ok(example),
        404: {"description": "Object not found", "content": {"application/json": {"example": ex.ERROR_404_EXAMPLE}}},
    }


def _not_found(type_name: str, db_id: uuid.UUID) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"type": "https://schema.oparl.org/1.1/Error", "name": "Not Found", "message": f"No {type_name} with id {db_id}."},
    )


def _external_list(
    session: Session,
    model: type,
    serialize_fn: Callable[[Any], dict],
    list_url: str,
    page: int,
    page_size: int,
    filters: TimeFilters,
) -> JSONResponse:
    items, total = list_objects(session, model, page, page_size, filters)
    data = [serialize_fn(o) for o in items]
    return JSONResponse(make_list_envelope(data, total, page, page_size, list_url))


# --- System ----------------------------------------------------------------
@router.get("/system", tags=[TAG_SYSTEM], summary="OParl entry point (System object)", responses=_ok(ex.SYSTEM_EXAMPLE))
def get_system(settings: SettingsDep, session: SessionDep) -> JSONResponse:
    """The OParl `System` object. Start here: its `body` field links to the body list."""
    serializer = OParlSerializer(settings.base_url, _default_body_db_id(session))
    system = session.exec(select(System)).first()
    blist = body_list_url(settings.base_url)
    if system is None:
        # Synthesize a minimal valid System from settings if none is stored yet.
        data = {
            "id": system_url(settings.base_url),
            "type": "https://schema.oparl.org/1.1/System",
            "oparlVersion": settings.oparl_version,
            "name": settings.system_name,
            "body": blist,
            "contactEmail": settings.contact_email,
            "contactName": settings.contact_name,
            "website": settings.website,
            "vendor": settings.vendor,
            "product": settings.product,
            "license": settings.license,
        }
        data = {k: v for k, v in data.items() if v is not None}
        return JSONResponse(data)
    return JSONResponse(serializer.serialize_system(system, blist))


# --- Body -------------------------------------------------------------------
@router.get("/bodies", tags=[TAG_BODY], summary="List bodies", responses=_ok(ex.list_example(ex.BODY_EXAMPLE, total=1)))
def list_bodies(
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    """Paginated external list of `Body` objects."""
    terms = list(session.exec(select(LegislativeTerm)).all())
    return _external_list(
        session,
        Body,
        lambda b: serializer.serialize_body(b, terms),
        body_list_url(settings.base_url),
        page,
        settings.page_size,
        filters,
    )


@router.get("/bodies/{db_id}", tags=[TAG_BODY], summary="Get a body", responses=_ok_obj(ex.BODY_EXAMPLE))
def get_body(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    body = get_by_id(session, Body, db_id)
    if body is None:
        raise _not_found("Body", db_id)
    terms = list(session.exec(select(LegislativeTerm)).all())
    return JSONResponse(serializer.serialize_body(body, terms))


# --- Body external lists ----------------------------------------------------
@router.get(
    "/bodies/{db_id}/organizations",
    tags=[TAG_LISTS],
    summary="List organizations of a body",
    responses=_ok(ex.list_example(ex.ORGANIZATION_EXAMPLE)),
)
def list_body_organizations(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        Organization,
        serializer.serialize_organization,
        body_sublist_url(settings.base_url, db_id, Organization),
        page,
        settings.page_size,
        filters,
    )


@router.get(
    "/bodies/{db_id}/people",
    tags=[TAG_LISTS],
    summary="List people of a body",
    responses=_ok(ex.list_example(ex.PERSON_EXAMPLE, total=771)),
)
def list_body_people(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session, Person, serializer.serialize_person, body_sublist_url(settings.base_url, db_id, Person), page, settings.page_size, filters
    )


@router.get(
    "/bodies/{db_id}/meetings",
    tags=[TAG_LISTS],
    summary="List meetings of a body",
    responses=_ok(ex.list_example(ex.MEETING_EXAMPLE, total=113)),
)
def list_body_meetings(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        Meeting,
        serializer.serialize_meeting,
        body_sublist_url(settings.base_url, db_id, Meeting),
        page,
        settings.page_size,
        filters,
    )


@router.get(
    "/bodies/{db_id}/papers", tags=[TAG_LISTS], summary="List papers of a body", responses=_ok(ex.list_example(ex.PAPER_EXAMPLE, total=19))
)
def list_body_papers(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session, Paper, serializer.serialize_paper, body_sublist_url(settings.base_url, db_id, Paper), page, settings.page_size, filters
    )


@router.get(
    "/bodies/{db_id}/agendaItems",
    tags=[TAG_LISTS],
    summary="List agenda items of a body",
    responses=_ok(ex.list_example(ex.AGENDA_ITEM_EXAMPLE)),
)
def list_body_agenda_items(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        AgendaItem,
        serializer.serialize_agenda_item,
        body_sublist_url(settings.base_url, db_id, AgendaItem),
        page,
        settings.page_size,
        filters,
    )


@router.get(
    "/bodies/{db_id}/consultations",
    tags=[TAG_LISTS],
    summary="List consultations of a body",
    responses=_ok(ex.list_example(ex.CONSULTATION_EXAMPLE)),
)
def list_body_consultations(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        Consultation,
        serializer.serialize_consultation,
        body_sublist_url(settings.base_url, db_id, Consultation),
        page,
        settings.page_size,
        filters,
    )


@router.get("/bodies/{db_id}/files", tags=[TAG_LISTS], summary="List files of a body", responses=_ok(ex.list_example(ex.FILE_EXAMPLE)))
def list_body_files(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session, File, serializer.serialize_file, body_sublist_url(settings.base_url, db_id, File), page, settings.page_size, filters
    )


@router.get(
    "/bodies/{db_id}/locations",
    tags=[TAG_LISTS],
    summary="List locations of a body (locationList)",
    responses=_ok(ex.list_example(ex.LOCATION_EXAMPLE)),
)
def list_body_locations(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        Location,
        serializer.serialize_location,
        body_sublist_url(settings.base_url, db_id, Location),
        page,
        settings.page_size,
        filters,
    )


@router.get(
    "/bodies/{db_id}/memberships",
    tags=[TAG_LISTS],
    summary="List memberships of a body",
    responses=_ok(ex.list_example(ex.MEMBERSHIP_EXAMPLE)),
)
def list_body_memberships(
    db_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    serializer: SerializerDep,
    filters: FiltersDep,
    page: int = Query(1, ge=1, description="1-based page number."),
) -> JSONResponse:
    return _external_list(
        session,
        Membership,
        serializer.serialize_membership,
        body_sublist_url(settings.base_url, db_id, Membership),
        page,
        settings.page_size,
        filters,
    )


# --- Object endpoints -------------------------------------------------------
@router.get("/organizations/{db_id}", tags=[TAG_OBJECTS], summary="Get an organization", responses=_ok_obj(ex.ORGANIZATION_EXAMPLE))
def get_organization(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Organization, db_id)
    if obj is None:
        raise _not_found("Organization", db_id)
    return JSONResponse(serializer.serialize_organization(obj))


@router.get("/people/{db_id}", tags=[TAG_OBJECTS], summary="Get a person", responses=_ok_obj(ex.PERSON_EXAMPLE))
def get_person(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Person, db_id)
    if obj is None:
        raise _not_found("Person", db_id)
    return JSONResponse(serializer.serialize_person(obj))


@router.get("/memberships/{db_id}", tags=[TAG_OBJECTS], summary="Get a membership", responses=_ok_obj(ex.MEMBERSHIP_EXAMPLE))
def get_membership(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Membership, db_id)
    if obj is None:
        raise _not_found("Membership", db_id)
    return JSONResponse(serializer.serialize_membership(obj))


@router.get(
    "/meetings/{db_id}", tags=[TAG_OBJECTS], summary="Get a meeting (with embedded agenda items)", responses=_ok_obj(ex.MEETING_EXAMPLE)
)
def get_meeting(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Meeting, db_id)
    if obj is None:
        raise _not_found("Meeting", db_id)
    return JSONResponse(serializer.serialize_meeting(obj))


@router.get("/agendaItems/{db_id}", tags=[TAG_OBJECTS], summary="Get an agenda item", responses=_ok_obj(ex.AGENDA_ITEM_EXAMPLE))
def get_agenda_item(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, AgendaItem, db_id)
    if obj is None:
        raise _not_found("AgendaItem", db_id)
    return JSONResponse(serializer.serialize_agenda_item(obj))


@router.get("/papers/{db_id}", tags=[TAG_OBJECTS], summary="Get a paper", responses=_ok_obj(ex.PAPER_EXAMPLE))
def get_paper(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Paper, db_id)
    if obj is None:
        raise _not_found("Paper", db_id)
    return JSONResponse(serializer.serialize_paper(obj))


@router.get("/files/{db_id}", tags=[TAG_OBJECTS], summary="Get a file", responses=_ok_obj(ex.FILE_EXAMPLE))
def get_file(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, File, db_id)
    if obj is None:
        raise _not_found("File", db_id)
    return JSONResponse(serializer.serialize_file(obj))


@router.get("/locations/{db_id}", tags=[TAG_OBJECTS], summary="Get a location", responses=_ok_obj(ex.LOCATION_EXAMPLE))
def get_location(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Location, db_id)
    if obj is None:
        raise _not_found("Location", db_id)
    return JSONResponse(serializer.serialize_location(obj))


@router.get("/consultations/{db_id}", tags=[TAG_OBJECTS], summary="Get a consultation", responses=_ok_obj(ex.CONSULTATION_EXAMPLE))
def get_consultation(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, Consultation, db_id)
    if obj is None:
        raise _not_found("Consultation", db_id)
    return JSONResponse(serializer.serialize_consultation(obj))


@router.get(
    "/legislativeTerms/{db_id}", tags=[TAG_OBJECTS], summary="Get a legislative term", responses=_ok_obj(ex.LEGISLATIVE_TERM_EXAMPLE)
)
def get_legislative_term(db_id: uuid.UUID, session: SessionDep, serializer: SerializerDep) -> JSONResponse:
    obj = get_by_id(session, LegislativeTerm, db_id)
    if obj is None:
        raise _not_found("LegislativeTerm", db_id)
    return JSONResponse(serializer.serialize_legislative_term(obj))
