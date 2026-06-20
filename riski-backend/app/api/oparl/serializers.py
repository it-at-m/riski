from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.settings import BackendSettings
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
from sqlalchemy.inspection import inspect as sa_inspect

_EXCLUDED_FIELDS = {"db_id", "content", "embed"}


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _entity_url(settings: BackendSettings, resource: str, db_id: UUID | str) -> str:
    return f"{_normalize_base_url(settings.oparl_base_url)}/{resource}/{db_id}"


def _collection_url(settings: BackendSettings, resource: str) -> str:
    return f"{_normalize_base_url(settings.oparl_base_url)}/{resource}"


def _to_primitive(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_primitive(val) for key, val in value.items()}
    return value


def _extract_columns(entity: Any) -> dict[str, Any]:
    mapper = sa_inspect(entity.__class__)
    payload: dict[str, Any] = {}
    for column in mapper.column_attrs:
        key = column.key
        if key in _EXCLUDED_FIELDS:
            continue
        payload[key] = _to_primitive(getattr(entity, key))
    return payload


def _serialize_base(entity: Any, settings: BackendSettings, resource: str) -> dict[str, Any]:
    payload = _extract_columns(entity)
    original_id = payload.pop("id", None)
    if original_id and not payload.get("web"):
        payload["web"] = original_id
    payload["id"] = _entity_url(settings, resource=resource, db_id=entity.db_id)
    return {key: value for key, value in payload.items() if value is not None}


def _drop_internal_fields(payload: dict[str, Any], fields: tuple[str, ...], *, omit_internal: bool) -> None:
    if not omit_internal:
        return
    for field in fields:
        payload.pop(field, None)


def serialize_system(system: System, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(system, settings=settings, resource="system")
    payload["id"] = _collection_url(settings, "system")
    payload["body"] = _collection_url(settings, "body")

    other_versions = []
    for related in system.other_oparl_versions:
        if related.id:
            other_versions.append(related.id)
        else:
            other_versions.append(_entity_url(settings, resource="system", db_id=related.db_id))
    if other_versions:
        payload["otherOparlVersions"] = other_versions
    payload.pop("other_oparl_versions", None)
    return payload


def serialize_body(body: Body, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(body, settings=settings, resource="body")
    payload["organization"] = _collection_url(settings, "organization")
    payload["person"] = _collection_url(settings, "person")
    payload["meeting"] = _collection_url(settings, "meeting")
    payload["paper"] = _collection_url(settings, "paper")
    payload["agendaItem"] = _collection_url(settings, "agendaItem")
    payload["consultation"] = _collection_url(settings, "consultation")
    payload["file"] = _collection_url(settings, "file")
    payload["locationList"] = _collection_url(settings, "location")
    payload["legislativeTermList"] = _collection_url(settings, "legislativeTerm")
    payload["membership"] = _collection_url(settings, "membership")
    _drop_internal_fields(payload, ("legislativeTerm",), omit_internal=omit_internal)
    return payload


def serialize_organization(organization: Organization, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(organization, settings=settings, resource="organization")
    if organization.subOrganizationOf:
        payload["subOrganizationOf"] = _entity_url(settings, resource="organization", db_id=organization.subOrganizationOf)
    return payload


def serialize_person(person: Person, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(person, settings=settings, resource="person")
    if person.location:
        payload["location"] = _entity_url(settings, resource="location", db_id=person.location)
    if not omit_internal:
        payload["membership"] = [
            serialize_membership(membership, settings=settings, omit_internal=omit_internal) for membership in person.membership
        ]
    _drop_internal_fields(payload, ("membership",), omit_internal=omit_internal)
    return payload


def serialize_membership(membership: Membership, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(membership, settings=settings, resource="membership")
    if membership.organization:
        payload["organization"] = _entity_url(settings, resource="organization", db_id=membership.organization)
    return payload


def serialize_legislative_term(
    legislative_term: LegislativeTerm, settings: BackendSettings, *, omit_internal: bool = False
) -> dict[str, Any]:
    payload = _serialize_base(legislative_term, settings=settings, resource="legislativeTerm")
    return payload


def serialize_meeting(meeting: Meeting, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(meeting, settings=settings, resource="meeting")
    if meeting.invitation:
        payload["invitation"] = _entity_url(settings, resource="file", db_id=meeting.invitation)
    if meeting.resultsProtocol:
        payload["resultsProtocol"] = _entity_url(settings, resource="file", db_id=meeting.resultsProtocol)
    if meeting.verbatimProtocol:
        payload["verbatimProtocol"] = _entity_url(settings, resource="file", db_id=meeting.verbatimProtocol)
    if not omit_internal:
        payload["agendaItem"] = [
            serialize_agenda_item(agenda_item, settings=settings, omit_internal=omit_internal) for agenda_item in meeting.agenda_items
        ]
        payload["auxiliaryFile"] = [
            serialize_file(file_obj, settings=settings, omit_internal=omit_internal) for file_obj in meeting.auxiliary_files
        ]
    _drop_internal_fields(payload, ("agendaItem", "auxiliaryFile"), omit_internal=omit_internal)
    return payload


def serialize_agenda_item(agenda_item: AgendaItem, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(agenda_item, settings=settings, resource="agendaItem")
    if agenda_item.meeting:
        payload["meeting"] = _entity_url(settings, resource="meeting", db_id=agenda_item.meeting)
    if agenda_item.resolutionFile:
        payload["resolutionFile"] = _entity_url(settings, resource="file", db_id=agenda_item.resolutionFile)
    _drop_internal_fields(payload, ("auxiliaryFile",), omit_internal=omit_internal)
    return payload


def serialize_paper(paper: Paper, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(paper, settings=settings, resource="paper")
    if paper.mainFile_id:
        payload["mainFile"] = _entity_url(settings, resource="file", db_id=paper.mainFile_id)
    payload.pop("mainFile_id", None)
    if not omit_internal:
        payload["auxiliaryFile"] = [
            serialize_file(file_obj, settings=settings, omit_internal=omit_internal) for file_obj in paper.auxiliary_files
        ]
        payload["location"] = [serialize_location(location, settings=settings, omit_internal=omit_internal) for location in paper.locations]
    _drop_internal_fields(payload, ("auxiliaryFile", "location"), omit_internal=omit_internal)
    return payload


def serialize_file(file_obj: File, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(file_obj, settings=settings, resource="file")
    return payload


def serialize_consultation(consultation: Consultation, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(consultation, settings=settings, resource="consultation")
    if consultation.paper:
        payload["paper"] = _entity_url(settings, resource="paper", db_id=consultation.paper)
    if consultation.agenda_item:
        payload["agendaItem"] = _entity_url(settings, resource="agendaItem", db_id=consultation.agenda_item)
    if consultation.meeting:
        payload["meeting"] = _entity_url(settings, resource="meeting", db_id=consultation.meeting)
    payload.pop("agenda_item", None)
    return payload


def serialize_location(location: Location, settings: BackendSettings, *, omit_internal: bool = False) -> dict[str, Any]:
    payload = _serialize_base(location, settings=settings, resource="location")
    return payload
