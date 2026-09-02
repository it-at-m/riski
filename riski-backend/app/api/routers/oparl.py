from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.dependencies import get_db_session
from app.api.oparl.filters import apply_common_filters
from app.api.oparl.pagination import build_paginated_response
from app.api.oparl.serializers import (
    serialize_agenda_item,
    serialize_body,
    serialize_consultation,
    serialize_file,
    serialize_legislative_term,
    serialize_location,
    serialize_meeting,
    serialize_membership,
    serialize_organization,
    serialize_paper,
    serialize_person,
    serialize_system,
)
from app.core.settings import BackendSettings, get_settings
from app.models.oparl import OParlListResponse
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
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

router = APIRouter(prefix="/api/oparl/v1.1", tags=["oparl"])


def _settings() -> BackendSettings:
    return get_settings()


@router.get("/system", response_model=dict[str, Any])
async def get_system(
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return the OParl system entrypoint object."""
    system = (await session.execute(select(System).order_by(System.db_id).limit(1))).scalars().first()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No system object found")
    return serialize_system(system, settings=settings)


@router.get("/body", response_model=OParlListResponse[dict[str, Any]])
async def list_body(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of bodies."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Body).order_by(Body.db_id),
        model=Body,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Body,
        serializer=lambda body: serialize_body(body, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/body/{body_id}", response_model=dict[str, Any])
async def get_body(
    body_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single body object by internal UUID."""
    body = (await session.execute(select(Body).where(Body.db_id == body_id).limit(1))).scalars().first()
    if body is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Body not found")
    return serialize_body(body, settings=settings)


@router.get("/organization", response_model=OParlListResponse[dict[str, Any]])
async def list_organization(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of organizations."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Organization).order_by(Organization.db_id),
        model=Organization,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Organization,
        serializer=lambda organization: serialize_organization(organization, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/organization/{organization_id}", response_model=dict[str, Any])
async def get_organization(
    organization_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single organization object by internal UUID."""
    organization = (await session.execute(select(Organization).where(Organization.db_id == organization_id).limit(1))).scalars().first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return serialize_organization(organization, settings=settings)


@router.get("/person", response_model=OParlListResponse[dict[str, Any]])
async def list_person(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of persons."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Person).options(selectinload(Person.membership)).order_by(Person.db_id),
        model=Person,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Person,
        serializer=lambda person: serialize_person(person, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/person/{person_id}", response_model=dict[str, Any])
async def get_person(
    person_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single person object by internal UUID."""
    person = (
        (await session.execute(select(Person).where(Person.db_id == person_id).options(selectinload(Person.membership)).limit(1)))
        .scalars()
        .first()
    )
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return serialize_person(person, settings=settings)


@router.get("/membership", response_model=OParlListResponse[dict[str, Any]])
async def list_membership(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of memberships."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Membership).order_by(Membership.db_id),
        model=Membership,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Membership,
        serializer=lambda membership: serialize_membership(membership, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/membership/{membership_id}", response_model=dict[str, Any])
async def get_membership(
    membership_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single membership object by internal UUID."""
    membership = (await session.execute(select(Membership).where(Membership.db_id == membership_id).limit(1))).scalars().first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    return serialize_membership(membership, settings=settings)


@router.get("/legislativeTerm", response_model=OParlListResponse[dict[str, Any]])
async def list_legislative_term(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of legislative terms."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(LegislativeTerm).order_by(LegislativeTerm.db_id),
        model=LegislativeTerm,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=LegislativeTerm,
        serializer=lambda legislative_term: serialize_legislative_term(legislative_term, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/legislativeTerm/{legislative_term_id}", response_model=dict[str, Any])
async def get_legislative_term(
    legislative_term_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single legislative term object by internal UUID."""
    legislative_term = (
        (await session.execute(select(LegislativeTerm).where(LegislativeTerm.db_id == legislative_term_id).limit(1))).scalars().first()
    )
    if legislative_term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LegislativeTerm not found")
    return serialize_legislative_term(legislative_term, settings=settings)


@router.get("/meeting", response_model=OParlListResponse[dict[str, Any]])
async def list_meeting(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of meetings."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Meeting)
        .options(selectinload(Meeting.agenda_items), selectinload(Meeting.auxiliary_files))
        .order_by(Meeting.db_id),
        model=Meeting,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Meeting,
        serializer=lambda meeting: serialize_meeting(meeting, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/meeting/{meeting_id}", response_model=dict[str, Any])
async def get_meeting(
    meeting_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single meeting object by internal UUID."""
    meeting = (
        (
            await session.execute(
                select(Meeting)
                .where(Meeting.db_id == meeting_id)
                .options(selectinload(Meeting.agenda_items), selectinload(Meeting.auxiliary_files))
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return serialize_meeting(meeting, settings=settings)


@router.get("/agendaItem", response_model=OParlListResponse[dict[str, Any]])
async def list_agenda_item(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of agenda items."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(AgendaItem).order_by(AgendaItem.db_id),
        model=AgendaItem,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=AgendaItem,
        serializer=lambda agenda_item: serialize_agenda_item(agenda_item, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/agendaItem/{agenda_item_id}", response_model=dict[str, Any])
async def get_agenda_item(
    agenda_item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single agenda item object by internal UUID."""
    agenda_item = (await session.execute(select(AgendaItem).where(AgendaItem.db_id == agenda_item_id).limit(1))).scalars().first()
    if agenda_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AgendaItem not found")
    return serialize_agenda_item(agenda_item, settings=settings)


@router.get("/paper", response_model=OParlListResponse[dict[str, Any]])
async def list_paper(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of papers."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Paper).options(selectinload(Paper.auxiliary_files), selectinload(Paper.locations)).order_by(Paper.db_id),
        model=Paper,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Paper,
        serializer=lambda paper: serialize_paper(paper, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/paper/{paper_id}", response_model=dict[str, Any])
async def get_paper(
    paper_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single paper object by internal UUID."""
    paper = (
        (
            await session.execute(
                select(Paper)
                .where(Paper.db_id == paper_id)
                .options(selectinload(Paper.auxiliary_files), selectinload(Paper.locations))
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return serialize_paper(paper, settings=settings)


@router.get("/file", response_model=OParlListResponse[dict[str, Any]])
async def list_file(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of files."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(File).order_by(File.db_id),
        model=File,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=File,
        serializer=lambda file_obj: serialize_file(file_obj, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/file/{file_id}", response_model=dict[str, Any])
async def get_file(
    file_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single file object by internal UUID."""
    file_obj = (await session.execute(select(File).where(File.db_id == file_id).limit(1))).scalars().first()
    if file_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return serialize_file(file_obj, settings=settings)


@router.get("/consultation", response_model=OParlListResponse[dict[str, Any]])
async def list_consultation(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of consultations."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Consultation).order_by(Consultation.db_id),
        model=Consultation,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Consultation,
        serializer=lambda consultation: serialize_consultation(consultation, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/consultation/{consultation_id}", response_model=dict[str, Any])
async def get_consultation(
    consultation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single consultation object by internal UUID."""
    consultation = (await session.execute(select(Consultation).where(Consultation.db_id == consultation_id).limit(1))).scalars().first()
    if consultation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    return serialize_consultation(consultation, settings=settings)


@router.get("/location", response_model=OParlListResponse[dict[str, Any]])
async def list_location(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1),
    created_since: datetime | None = Query(default=None),
    created_until: datetime | None = Query(default=None),
    modified_since: datetime | None = Query(default=None),
    modified_until: datetime | None = Query(default=None),
    omit_internal: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> OParlListResponse[dict[str, Any]]:
    """Return a paginated OParl external list of locations."""
    page_size = settings.oparl_page_size_default if limit is None else limit
    base_query = apply_common_filters(
        base_query=select(Location).order_by(Location.db_id),
        model=Location,
        created_since=created_since,
        created_until=created_until,
        modified_since=modified_since,
        modified_until=modified_until,
    )
    return await build_paginated_response(
        request=request,
        session=session,
        base_query=base_query,
        count_from=Location,
        serializer=lambda location: serialize_location(location, settings=settings, omit_internal=omit_internal),
        page=page,
        limit=page_size,
        settings=settings,
    )


@router.get("/location/{location_id}", response_model=dict[str, Any])
async def get_location(
    location_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: BackendSettings = Depends(_settings),
) -> dict[str, Any]:
    """Return a single location object by internal UUID."""
    location = (await session.execute(select(Location).where(Location.db_id == location_id).limit(1))).scalars().first()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return serialize_location(location, settings=settings)
