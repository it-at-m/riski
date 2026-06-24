"""Curated OParl example payloads for the OpenAPI / Swagger UI documentation.

These mirror the structure produced by ``serializers.py``. They are documentation
only — the live responses are generated dynamically from the database. A fixed
example host is used so the examples read clearly.
"""

from typing import Any

_H = "https://oparl.example.org/oparl/v1"

SYSTEM_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/system",
    "type": "https://schema.oparl.org/1.1/System",
    "oparlVersion": "https://schema.oparl.org/1.1/",
    "name": "RISKI OParl Schnittstelle",
    "body": f"{_H}/bodies",
    "website": "https://risi.muenchen.de/risi",
    "vendor": "https://github.com/it-at-m/riski",
    "product": "https://github.com/it-at-m/riski",
    "license": "https://www.govdata.de/dl-de/by-2-0",
}

BODY_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261",
    "type": "https://schema.oparl.org/1.1/Body",
    "system": f"{_H}/system",
    "name": "Landeshauptstadt München",
    "shortName": "München",
    "website": "https://risi.muenchen.de/risi",
    "license": "https://www.govdata.de/dl-de/by-2-0",
    "organization": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/organizations",
    "person": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/people",
    "meeting": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/meetings",
    "paper": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/papers",
    "agendaItem": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/agendaItems",
    "consultation": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/consultations",
    "file": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/files",
    "locationList": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/locations",
    "membership": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261/memberships",
    "legislativeTerm": [],
    "created": "2026-06-24T15:47:08+02:00",
    "modified": "2026-06-24T15:47:08+02:00",
}

ORGANIZATION_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/organizations/3a1b8e10-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/Organization",
    "body": f"{_H}/bodies/dbf2fbcb-38b4-4334-93fa-875f9963b261",
    "name": "Fraktion Beispiel",
    "shortName": "FB",
    "organizationType": "Fraktion",
    "classification": "Fraktion",
    "membership": [f"{_H}/memberships/9c1f0000-0000-4000-8000-000000000001"],
}

PERSON_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/people/3c3f9342-741a-4eb6-b15d-037d60fda0a1",
    "type": "https://schema.oparl.org/1.1/Person",
    "web": "https://risi.muenchen.de/risi/person/detail/12345",
    "name": "Dr. Maria Musterfrau",
    "familyName": "Musterfrau",
    "givenName": "Maria",
    "formOfAddress": "Frau",
    "title": ["Dr."],
    "status": ["Stadträtin"],
    "membership": [f"{_H}/memberships/9c1f0000-0000-4000-8000-000000000001"],
}

MEMBERSHIP_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/memberships/9c1f0000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/Membership",
    "person": f"{_H}/people/3c3f9342-741a-4eb6-b15d-037d60fda0a1",
    "organization": f"{_H}/organizations/3a1b8e10-0000-4000-8000-000000000001",
    "role": "Mitglied",
    "votingRight": True,
    "startDate": "2020-05-01",
}

MEETING_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/meetings/7b2c0000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/Meeting",
    "web": "https://risi.muenchen.de/risi/sitzung/detail/67890",
    "name": "Vollversammlung des Stadtrats",
    "meetingState": "conducted",
    "cancelled": False,
    "start": "2026-03-05T09:00:00",
    "end": "2026-03-05T13:30:00",
    "organization": [f"{_H}/organizations/3a1b8e10-0000-4000-8000-000000000001"],
    "agendaItem": [
        {
            "id": f"{_H}/agendaItems/aa110000-0000-4000-8000-000000000001",
            "type": "https://schema.oparl.org/1.1/AgendaItem",
            "number": "1",
            "order": 0,
            "name": "Begrüßung",
            "public": True,
        }
    ],
}

AGENDA_ITEM_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/agendaItems/aa110000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/AgendaItem",
    "meeting": f"{_H}/meetings/7b2c0000-0000-4000-8000-000000000001",
    "number": "1",
    "order": 0,
    "name": "Begrüßung",
    "public": True,
}

PAPER_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/papers/32d05f75-2e09-4568-b4f2-3d21bf4af3f3",
    "type": "https://schema.oparl.org/1.1/Paper",
    "web": "https://risi.muenchen.de/risi/sitzungsvorlage/detail/205451",
    "name": "Sitzungsvorlage zur Verkehrsberuhigung",
    "reference": "02-08 / V 00516",
    "date": "2026-03-05",
    "paperType": "Sitzungsvorlage",
    "mainFile": f"{_H}/files/195f2cfe-ff05-4d51-a934-fb78a697dc1a",
    "auxiliaryFile": [f"{_H}/files/ecf694ba-8f44-4fae-b9fd-6e3d6f888708"],
    "originatorPerson": [f"{_H}/people/3c3f9342-741a-4eb6-b15d-037d60fda0a1"],
}

FILE_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/files/195f2cfe-ff05-4d51-a934-fb78a697dc1a",
    "type": "https://schema.oparl.org/1.1/File",
    "name": "Beschlussvorlage",
    "fileName": "vorlage.pdf",
    "mimeType": "application/pdf",
    "accessUrl": "https://risi.muenchen.de/risi/dokument/205451.pdf",
    "downloadUrl": "https://risi.muenchen.de/risi/dokument/205451.pdf",
}

LOCATION_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/locations/cc330000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/Location",
    "description": "Rathaus, Marienplatz 8, 80331 München",
    "streetAddress": "Marienplatz 8",
    "postalCode": "80331",
    "locality": "München",
}

CONSULTATION_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/consultations/dd440000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/Consultation",
    "paper": f"{_H}/papers/32d05f75-2e09-4568-b4f2-3d21bf4af3f3",
    "meeting": f"{_H}/meetings/7b2c0000-0000-4000-8000-000000000001",
    "authoritative": True,
    "role": "Beschlussfassung",
}

LEGISLATIVE_TERM_EXAMPLE: dict[str, Any] = {
    "id": f"{_H}/legislativeTerms/ee550000-0000-4000-8000-000000000001",
    "type": "https://schema.oparl.org/1.1/LegislativeTerm",
    "name": "Wahlperiode 2020–2026",
    "startDate": "2020-05-01",
    "endDate": "2026-04-30",
}


def list_example(item_example: dict[str, Any], total: int = 19) -> dict[str, Any]:
    """Wrap an object example in the OParl external-list envelope."""
    return {
        "data": [item_example],
        "pagination": {"totalElements": total, "elementsPerPage": 50, "currentPage": 1, "totalPages": 1},
        "links": {"first": f"{_H}/list?page=1", "last": f"{_H}/list?page=1"},
    }


ERROR_404_EXAMPLE: dict[str, Any] = {
    "detail": {
        "type": "https://schema.oparl.org/1.1/Error",
        "name": "Not Found",
        "message": "No Paper with id 00000000-0000-0000-0000-000000000000.",
    }
}
