"""Canonical OParl URL construction.

In OParl every object's ``id`` is a dereferenceable URL on *this* API. We derive
those URLs from the database primary key (``db_id``); the original RIS source URL
(stored in the DB ``id`` field) is published in the OParl ``web`` field instead.

This module is the single source of truth for the URL layout.
"""

import uuid

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

# Model class -> URL path segment for object endpoints.
TYPE_PATHS: dict[type, str] = {
    Body: "bodies",
    Organization: "organizations",
    Person: "people",
    Membership: "memberships",
    Meeting: "meetings",
    AgendaItem: "agendaItems",
    Paper: "papers",
    File: "files",
    Location: "locations",
    Consultation: "consultations",
    LegislativeTerm: "legislativeTerms",
}

# Body sub-list endpoints (external lists) and their path segment.
# OParl 1.1 mandates organization, person, meeting, paper, agendaItem,
# consultation, file, locationList and membership as external list URLs.
BODY_LIST_PATHS = {
    Organization: "organizations",
    Person: "people",
    Meeting: "meetings",
    Paper: "papers",
    AgendaItem: "agendaItems",
    Consultation: "consultations",
    File: "files",
    Location: "locations",
    Membership: "memberships",
}


def object_url(base_url: str, model: type, db_id: uuid.UUID | str) -> str:
    """URL of a single object of ``model`` with the given primary key."""
    return f"{base_url}/{TYPE_PATHS[model]}/{db_id}"


def system_url(base_url: str) -> str:
    return f"{base_url}/system"


def body_list_url(base_url: str) -> str:
    return f"{base_url}/bodies"


def body_sublist_url(base_url: str, body_db_id: uuid.UUID | str, model: type) -> str:
    """URL of an external list scoped to a body, e.g. ``/bodies/{id}/papers``."""
    return f"{base_url}/bodies/{body_db_id}/{BODY_LIST_PATHS[model]}"
