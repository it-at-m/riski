"""Serialization of RISKI data-model objects into OParl 1.1 JSON.

Each serializer produces a plain ``dict`` ready for JSON output. Conventions:

* ``id`` is the canonical OParl URL derived from ``db_id`` (see ``urls.py``).
* ``type`` is taken from the stored schema URL on the object.
* The original RIS source URL is published as ``web``.
* Related objects are rendered as URL references (not embedded), except where
  OParl mandates embedding (Body.legislativeTerm, Meeting.agendaItem).
* ``None`` values and empty collections are omitted.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

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
)

# OParl date-time fields must carry a UTC offset. The DB stores naive local
# timestamps (datetime.now()), so we attach the server's local offset on output.
from app.oparl.mappings import map_meeting_state
from app.oparl.urls import body_sublist_url, object_url, system_url


def _dt(value: datetime | None) -> str | None:
    """OParl date-time: ``yyyy-mm-ddThh:mm:ss±hh:mm`` (with UTC offset)."""
    if not value:
        return None
    if value.tzinfo is None:
        # Naive timestamps are interpreted in the server's local timezone.
        value = value.astimezone()
    return value.isoformat()


def _date(value: datetime | date | None) -> str | None:
    """OParl date (YYYY-MM-DD)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def _enum_value(value: Any) -> Any:
    """Enum-typed columns are stored as plain strings, so DB reads return ``str``
    while freshly built objects hold the ``Enum``. Normalise both to the value."""
    return value.value if isinstance(value, Enum) else value


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    """Drop None values and empty lists/strings (OParl: omit empty optionals)."""
    return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


class OParlSerializer:
    """Stateless-ish serializer. Holds the base URL and the default body URL so
    objects can reference the body they belong to."""

    def __init__(self, base_url: str, body_db_id: uuid.UUID | None = None) -> None:
        self.base_url = base_url
        self.body_db_id = body_db_id
        self.body_url = object_url(base_url, Body, body_db_id) if body_db_id else None

    # --- helpers -----------------------------------------------------------
    def _ref(self, obj: Any) -> str | None:
        """URL reference to a related, persisted object."""
        if obj is None:
            return None
        return object_url(self.base_url, type(obj), obj.db_id)

    def _refs(self, objs: list[Any] | None) -> list[str]:
        return [self._ref(o) for o in (objs or []) if o is not None]

    def _fk_ref(self, model: type, fk: uuid.UUID | None) -> str | None:
        return object_url(self.base_url, model, fk) if fk else None

    @staticmethod
    def _web(obj: Any) -> str | None:
        src = getattr(obj, "web", None) or getattr(obj, "id", None)
        return src if isinstance(src, str) and src.startswith("http") else None

    def _base(self, obj: Any, self_url: str) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self_url, "type": obj.type}
        d["web"] = self._web(obj)
        d["created"] = _dt(getattr(obj, "created", None))
        d["modified"] = _dt(getattr(obj, "modified", None))
        if getattr(obj, "license", None):
            d["license"] = obj.license
        if getattr(obj, "deleted", None):
            d["deleted"] = obj.deleted
        return d

    # --- System / Body -----------------------------------------------------
    def serialize_system(self, system: Any, body_list_url: str) -> dict[str, Any]:
        d = self._base(system, system_url(self.base_url))
        d.update(
            {
                "oparlVersion": getattr(system, "oparlVersion", None),
                "name": getattr(system, "name", None),
                "body": body_list_url,
                "contactEmail": getattr(system, "contactEmail", None),
                "contactName": getattr(system, "contactName", None),
                "website": getattr(system, "website", None),
                "vendor": getattr(system, "vendor", None),
                "product": getattr(system, "product", None),
            }
        )
        return _clean(d)

    def serialize_body(self, body: Body, legislative_terms: list[LegislativeTerm] | None = None) -> dict[str, Any]:
        self_url = object_url(self.base_url, Body, body.db_id)
        d = self._base(body, self_url)
        d.update(
            {
                "system": system_url(self.base_url),
                "name": body.name,
                "shortName": body.shortName,
                "website": body.website,
                "ags": body.ags,
                "rgs": body.rgs,
                "classification": body.classification,
                "contactEmail": body.contactEmail,
                "contactName": body.contactName,
                "licenseValidSince": _dt(body.licenseValidSince),
                "oparlSince": _dt(body.oparlSince),
                "organization": body_sublist_url(self.base_url, body.db_id, Organization),
                "person": body_sublist_url(self.base_url, body.db_id, Person),
                "meeting": body_sublist_url(self.base_url, body.db_id, Meeting),
                "paper": body_sublist_url(self.base_url, body.db_id, Paper),
                "agendaItem": body_sublist_url(self.base_url, body.db_id, AgendaItem),
                "consultation": body_sublist_url(self.base_url, body.db_id, Consultation),
                "file": body_sublist_url(self.base_url, body.db_id, File),
                "locationList": body_sublist_url(self.base_url, body.db_id, Location),
                "membership": body_sublist_url(self.base_url, body.db_id, Membership),
            }
        )
        cleaned = _clean(d)
        # OParl requires legislativeTerm to be present as an (embedded) array,
        # even when empty, so it is added after dropping empty optionals.
        cleaned["legislativeTerm"] = [self.serialize_legislative_term(t) for t in (legislative_terms or [])]
        return cleaned

    # --- Organization / Person / Membership --------------------------------
    def serialize_organization(self, org: Organization) -> dict[str, Any]:
        self_url = object_url(self.base_url, Organization, org.db_id)
        d = self._base(org, self_url)
        org_type = _enum_value(org.organizationType)
        classification = _enum_value(org.classification)
        d.update(
            {
                "body": self.body_url,
                "name": org.name,
                "shortName": org.shortName,
                "organizationType": org_type,
                "classification": classification,
                "startDate": _date(org.startDate),
                "endDate": _date(org.endDate),
                "website": org.website,
                "subOrganizationOf": self._fk_ref(Organization, org.subOrganizationOf),
                "location": self._fk_ref(Location, org.location),
                "externalBody": org.externalBody,
                "membership": self._refs(org.membership),
            }
        )
        return _clean(d)

    def serialize_person(self, person: Person) -> dict[str, Any]:
        self_url = object_url(self.base_url, Person, person.db_id)
        d = self._base(person, self_url)
        d.update(
            {
                "body": self.body_url,
                "name": person.name,
                "familyName": person.familyName,
                "givenName": person.givenName,
                "formOfAddress": person.formOfAddress,
                "affix": person.affix,
                "title": [person.title] if person.title else [],
                "gender": person.gender,
                "status": list(person.status or []),
                "email": list(person.email or []),
                "phone": list(person.phone or []),
                "life": person.life,
                "lifeSource": person.lifeSource,
                "location": self._fk_ref(Location, person.location),
                "membership": self._refs(person.membership),
            }
        )
        return _clean(d)

    def serialize_membership(self, m: Membership) -> dict[str, Any]:
        self_url = object_url(self.base_url, Membership, m.db_id)
        d = self._base(m, self_url)
        person = m.person[0] if m.person else None
        organization = m.organizations[0] if m.organizations else None
        d.update(
            {
                "person": self._ref(person),
                "organization": self._ref(organization),
                "role": m.role,
                "votingRight": m.votingRight,
                "startDate": _date(m.startDate),
                "endDate": _date(m.endDate),
                "onBehalfOf": m.onBehalfOf,
            }
        )
        return _clean(d)

    # --- Meeting / AgendaItem ----------------------------------------------
    def serialize_meeting(self, meeting: Meeting) -> dict[str, Any]:
        self_url = object_url(self.base_url, Meeting, meeting.db_id)
        d = self._base(meeting, self_url)
        location = meeting.locations[0] if meeting.locations else None
        d.update(
            {
                "name": meeting.name,
                "meetingState": map_meeting_state(meeting.meetingState),
                "cancelled": meeting.cancelled,
                "start": _dt(meeting.start),
                "end": _dt(meeting.end),
                "location": self._ref(location),
                "organization": self._refs(meeting.organizations),
                "participant": self._refs(meeting.participants),
                "invitation": self._fk_ref(File, meeting.invitation),
                "resultsProtocol": self._fk_ref(File, meeting.resultsProtocol),
                "verbatimProtocol": self._fk_ref(File, meeting.verbatimProtocol),
                "auxiliaryFile": self._refs(meeting.auxiliary_files),
                # OParl embeds agendaItem objects in the meeting.
                "agendaItem": [self.serialize_agenda_item(a, embedded=True) for a in (meeting.agenda_items or [])],
            }
        )
        return _clean(d)

    def serialize_agenda_item(self, item: AgendaItem, embedded: bool = False) -> dict[str, Any]:
        self_url = object_url(self.base_url, AgendaItem, item.db_id)
        d = self._base(item, self_url)
        d.update(
            {
                "name": item.name,
                "number": item.number,
                # order is mandatory in OParl 1.1; fall back to 0 when unknown.
                "order": item.order if item.order is not None else 0,
                "public": item.public,
                "result": item.result,
                "resolutionText": item.resolutionText,
                "resolutionFile": self._fk_ref(File, item.resolutionFile),
                "start": _dt(item.start),
                "end": _dt(item.end),
                "auxiliaryFile": self._refs(item.auxiliaryFile),
            }
        )
        # When retrieved individually the agenda item references its meeting.
        if not embedded:
            d["meeting"] = self._fk_ref(Meeting, item.meeting)
        return _clean(d)

    # --- Paper / File ------------------------------------------------------
    def serialize_paper(self, paper: Paper) -> dict[str, Any]:
        self_url = object_url(self.base_url, Paper, paper.db_id)
        d = self._base(paper, self_url)
        paper_type = _enum_value(paper.paper_type)
        d.update(
            {
                "body": self.body_url,
                "name": paper.name,
                "reference": paper.reference,
                "date": _date(paper.date),
                "paperType": paper_type,
                "mainFile": self._ref(paper.mainFile),
                "auxiliaryFile": self._refs(paper.auxiliary_files),
                "relatedPaper": self._refs(paper.related_papers),
                "superordinatedPaper": self._refs(paper.super_papers),
                "subordinatedPaper": self._refs(paper.sub_papers),
                "originatorPerson": self._refs(paper.originator_persons),
                "originatorOrganization": self._refs(paper.originator_orgs),
                "underDirectionOf": self._refs(paper.under_direction_of),
                "location": self._refs(paper.locations),
            }
        )
        return _clean(d)

    def serialize_file(self, file: File) -> dict[str, Any]:
        self_url = object_url(self.base_url, File, file.db_id)
        d = self._base(file, self_url)
        master = file.masterFile if isinstance(file.masterFile, str) and file.masterFile.startswith("http") else None
        d.update(
            {
                "name": file.name,
                "fileName": file.fileName,
                "mimeType": file.mimeType,
                "date": _date(file.date),
                "size": file.size,
                "sha1Checksum": file.sha1Checksum,
                "sha512Checksum": file.sha512Checksum,
                "text": file.text,
                "accessUrl": file.accessUrl,
                "downloadUrl": file.downloadUrl,
                "externalServiceUrl": file.externalServiceUrl,
                "masterFile": master,
                "derivativeFile": self._refs(file.derivative_files),
            }
        )
        if file.fileLicense:
            d["fileLicense"] = file.fileLicense
        return _clean(d)

    # --- Location / Consultation / LegislativeTerm -------------------------
    def serialize_location(self, loc: Location) -> dict[str, Any]:
        self_url = object_url(self.base_url, Location, loc.db_id)
        d = self._base(loc, self_url)
        d.update(
            {
                "description": loc.description,
                "geojson": loc.geojson,
                "streetAddress": loc.streetAddress,
                "room": loc.room,
                "postalCode": loc.postalCode,
                "subLocality": loc.subLocality,
                "locality": loc.locality,
            }
        )
        return _clean(d)

    def serialize_consultation(self, c: Consultation) -> dict[str, Any]:
        self_url = object_url(self.base_url, Consultation, c.db_id)
        d = self._base(c, self_url)
        d.update(
            {
                "paper": self._fk_ref(Paper, c.paper),
                "agendaItem": self._fk_ref(AgendaItem, c.agenda_item),
                "meeting": self._fk_ref(Meeting, c.meeting),
                "authoritative": c.authoritative,
                "role": c.role,
            }
        )
        return _clean(d)

    def serialize_legislative_term(self, term: LegislativeTerm) -> dict[str, Any]:
        self_url = object_url(self.base_url, LegislativeTerm, term.db_id)
        d = self._base(term, self_url)
        d.update(
            {
                "name": term.name,
                "startDate": _date(term.startDate),
                "endDate": _date(term.endDate),
            }
        )
        return _clean(d)
