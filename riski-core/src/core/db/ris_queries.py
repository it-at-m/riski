"""Structured RIS database queries for the agent.

This module intentionally exposes a small, explicit set of domain queries
instead of accepting arbitrary SQL from the LLM/backend.  The backend agent
wraps these functions in a LangChain tool.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from core.model.data_models import (
    Membership,
    Organization,
    OrganizationClassificationEnum,
    OrganizationMembership,
    OrganizationTypeEnum,
    Paper,
    PaperOriginatorPersonLink,
    PaperTypeEnum,
    Person,
    PersonMembershipLink,
)


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _person_to_dict(person: Person) -> dict[str, Any]:
    return {
        "id": str(person.db_id),
        "name": person.name,
        "givenName": person.givenName,
        "familyName": person.familyName,
        "web": person.web,
        "risUrl": person.id,
    }


def _organization_to_dict(org: Organization) -> dict[str, Any]:
    return {
        "id": str(org.db_id),
        "name": org.name,
        "shortName": org.shortName,
        "classification": _enum_value(org.classification),
        "organizationType": _enum_value(org.organizationType),
        "startDate": _iso(org.startDate),
        "endDate": _iso(org.endDate),
        "website": org.website,
        "web": org.web,
        "risUrl": org.id,
        "inactive": org.inactive,
    }


def _paper_to_dict(paper: Paper) -> dict[str, Any]:
    return {
        "id": str(paper.db_id),
        "reference": paper.reference,
        "name": paper.name,
        "subject": paper.subject,
        "short_information": paper.short_information,
        "description": paper.description,
        "date": _iso(paper.date),
        "paper_type": _enum_value(paper.paper_type),
        "paper_subtype": _enum_value(paper.paper_subtype),
        "web": paper.web,
        "risUrl": paper.id,
    }


def _person_name_filter(person_name: str):
    """Return a forgiving SQL filter for person name lookups."""
    compact_name = " ".join(person_name.strip().split())
    pattern = f"%{compact_name}%"

    return or_(
        Person.name.ilike(pattern),
        Person.familyName.ilike(pattern),
        Person.givenName.ilike(pattern),
        func.concat(
            func.coalesce(Person.givenName, ""),
            " ",
            func.coalesce(Person.familyName, ""),
        ).ilike(pattern),
        func.concat(
            func.coalesce(Person.familyName, ""),
            " ",
            func.coalesce(Person.givenName, ""),
        ).ilike(pattern),
    )


def _active_date_filter(start_col, end_col, at: datetime | None = None):
    """Filter records that are active at a point in time."""
    at = at or datetime.now()
    return and_(
        or_(start_col.is_(None), start_col <= at),
        or_(end_col.is_(None), end_col >= at),
    )


def _faction_filter():
    return or_(
        Organization.classification == OrganizationClassificationEnum.FACTION.value,
        Organization.organizationType == OrganizationTypeEnum.FACTION.value,
    )


async def list_factions(
    session: AsyncSession,
    include_inactive: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List factions from the organization table."""
    stmt = select(Organization).where(_faction_filter()).order_by(Organization.name).limit(limit)

    if not include_inactive:
        stmt = stmt.where(or_(Organization.inactive.is_(None), Organization.inactive.is_(False)))

    result = await session.execute(stmt)
    organizations = result.scalars().all()
    return [_organization_to_dict(org) for org in organizations]


async def find_persons(
    session: AsyncSession,
    person_name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find persons by a fuzzy-ish name match."""
    stmt = select(Person).where(_person_name_filter(person_name)).order_by(Person.familyName, Person.givenName).limit(limit)
    result = await session.execute(stmt)
    return [_person_to_dict(person) for person in result.scalars().all()]


async def _find_person_candidates(session: AsyncSession, person_name: str, limit: int = 5) -> list[Person]:
    stmt = select(Person).where(_person_name_filter(person_name)).order_by(Person.familyName, Person.givenName).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def person_factions(
    session: AsyncSession,
    person_name: str,
    at: datetime | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Return the factions in which a person is/was a member.

    The preferred path is Person -> PersonMembershipLink -> Membership.organization -> Organization.
    Some imports also populate OrganizationMembership, so a fallback path through that
    link table is queried as well and de-duplicated.
    """
    people = await _find_person_candidates(session, person_name)

    if not people:
        return {
            "status": "not_found",
            "message": f"Keine Person zu '{person_name}' gefunden.",
            "persons": [],
            "factions": [],
        }

    if len(people) > 1:
        return {
            "status": "ambiguous_person",
            "message": f"Mehrere Personen zu '{person_name}' gefunden.",
            "persons": [_person_to_dict(person) for person in people],
            "factions": [],
        }

    person = people[0]
    rows_by_key: dict[str, tuple[Organization, Membership]] = {}

    direct_stmt = (
        select(Organization, Membership)
        .join(Membership, Membership.organization == Organization.db_id)
        .join(PersonMembershipLink, PersonMembershipLink.membership_id == Membership.db_id)
        .where(PersonMembershipLink.person_id == person.db_id)
        .where(_faction_filter())
        .where(_active_date_filter(Membership.startDate, Membership.endDate, at))
        .order_by(Organization.name)
        .limit(limit)
    )
    direct_result = await session.execute(direct_stmt)
    for org, membership in direct_result.all():
        rows_by_key[f"{org.db_id}:{membership.db_id}"] = (org, membership)

    fallback_stmt = (
        select(Organization, Membership)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.db_id)
        .join(Membership, Membership.db_id == OrganizationMembership.membership_id)
        .join(PersonMembershipLink, PersonMembershipLink.membership_id == Membership.db_id)
        .where(PersonMembershipLink.person_id == person.db_id)
        .where(_faction_filter())
        .where(_active_date_filter(Membership.startDate, Membership.endDate, at))
        .order_by(Organization.name)
        .limit(limit)
    )
    fallback_result = await session.execute(fallback_stmt)
    for org, membership in fallback_result.all():
        rows_by_key[f"{org.db_id}:{membership.db_id}"] = (org, membership)

    factions = []
    for org, membership in rows_by_key.values():
        factions.append(
            {
                **_organization_to_dict(org),
                "role": membership.role,
                "votingRight": membership.votingRight,
                "membershipStartDate": _iso(membership.startDate),
                "membershipEndDate": _iso(membership.endDate),
                "onBehalfOf": membership.onBehalfOf,
            }
        )

    return {
        "status": "ok",
        "person": _person_to_dict(person),
        "factions": factions[:limit],
    }


async def person_papers(
    session: AsyncSession,
    person_name: str,
    paper_type: PaperTypeEnum | None = PaperTypeEnum.COUNCIL_PROPOSAL,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Return papers/proposals submitted by a person."""
    people = await _find_person_candidates(session, person_name)

    if not people:
        return {
            "status": "not_found",
            "message": f"Keine Person zu '{person_name}' gefunden.",
            "persons": [],
            "papers": [],
        }

    if len(people) > 1:
        return {
            "status": "ambiguous_person",
            "message": f"Mehrere Personen zu '{person_name}' gefunden.",
            "persons": [_person_to_dict(person) for person in people],
            "papers": [],
        }

    person = people[0]
    stmt = (
        select(Paper)
        .join(PaperOriginatorPersonLink, PaperOriginatorPersonLink.paper_id == Paper.db_id)
        .where(PaperOriginatorPersonLink.person_id == person.db_id)
        .order_by(Paper.date.desc().nullslast(), Paper.name)
        .limit(limit)
    )

    if paper_type is not None:
        stmt = stmt.where(Paper.paper_type == _enum_value(paper_type))
    if since is not None:
        stmt = stmt.where(Paper.date >= since)
    if until is not None:
        stmt = stmt.where(Paper.date <= until)

    result = await session.execute(stmt)
    papers = result.scalars().all()

    return {
        "status": "ok",
        "person": _person_to_dict(person),
        "papers": [_paper_to_dict(paper) for paper in papers],
        "filters": {
            "paper_type": _enum_value(paper_type),
            "since": _iso(since),
            "until": _iso(until),
            "limit": limit,
        },
    }


async def count_papers(
    session: AsyncSession,
    paper_type: PaperTypeEnum | None = PaperTypeEnum.COUNCIL_PROPOSAL,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict[str, Any]:
    """Count papers/proposals in a date range."""
    stmt = select(func.count(Paper.db_id))

    if paper_type is not None:
        stmt = stmt.where(Paper.paper_type == _enum_value(paper_type))
    if since is not None:
        stmt = stmt.where(Paper.date >= since)
    if until is not None:
        stmt = stmt.where(Paper.date <= until)

    result = await session.execute(stmt)
    count = result.scalar_one()

    return {
        "status": "ok",
        "count": int(count),
        "paper_type": _enum_value(paper_type),
        "since": _iso(since),
        "until": _iso(until),
    }
